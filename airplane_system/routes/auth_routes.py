# ============================================
# routes/auth_routes.py - Authentication Routes
# ============================================
# Concept: Blueprint = Related routes ka group
# Jaise auth ke liye: login, signup, logout, verify
# Yeh sab ek jagah organize hain
# ============================================

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from models import db, User

# Blueprint create karo
# 'auth' = blueprint ka naam
auth_bp = Blueprint('auth', __name__)


# ============================================
# SIGNUP ROUTE
# ============================================
@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    GET request: Form dikhao
    POST request: Form data process karo
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        # Form se data lo
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required!', 'error')
            return render_template('auth/signup.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'error')
            return render_template('auth/signup.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/signup.html')

        # Check karo email already exist karta hai ya nahi
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered! Please login.', 'error')
            return redirect(url_for('auth.login'))

        # Password hash karo (plain text kabhi store mat karo!)
        # Concept: generate_password_hash("abc123") = "$2b$12$xyz..."
        # Original password wapis nahi milta, sirf verify ho sakta hai
        hashed_password = generate_password_hash(password)

        # New user banao
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            is_verified=False
        )

        # OTP generate karo
        otp = new_user.generate_otp()

        # Database mein save karo
        db.session.add(new_user)
        db.session.commit()

        # OTP email bhejo (dummy - print karte hain)
        print(f"\n📧 OTP for {email}: {otp}\n")  # Development mein print
        send_otp_email(email, name, otp)

        # Session mein email save karo verification ke liye
        session['verify_email'] = email

        flash(f'Account created! OTP sent to {email}. Check console for OTP in demo mode.', 'success')
        return redirect(url_for('auth.verify_otp'))

    return render_template('auth/signup.html')


# ============================================
# OTP VERIFICATION ROUTE
# ============================================
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Email OTP verify karta hai"""
    email = session.get('verify_email')
    if not email:
        return redirect(url_for('auth.signup'))

    if request.method == 'POST':
        entered_otp = request.form.get('otp', '').strip()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('User not found!', 'error')
            return redirect(url_for('auth.signup'))

        # OTP expire check (10 minutes)
        if user.otp_created_at:
            time_diff = datetime.utcnow() - user.otp_created_at
            if time_diff > timedelta(minutes=10):
                flash('OTP expired! Please request a new one.', 'error')
                return render_template('auth/verify_otp.html', email=email)

        if user.otp == entered_otp:
            # Account verify karo
            user.is_verified = True
            user.otp = None  # OTP delete karo
            db.session.commit()

            session.pop('verify_email', None)
            flash('Email verified! You can now login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Invalid OTP! Please try again.', 'error')

    return render_template('auth/verify_otp.html', email=email)


# ============================================
# RESEND OTP ROUTE
# ============================================
@auth_bp.route('/resend-otp')
def resend_otp():
    """Naya OTP bhejta hai"""
    email = session.get('verify_email')
    if not email:
        return redirect(url_for('auth.signup'))

    user = User.query.filter_by(email=email).first()
    if user:
        otp = user.generate_otp()
        db.session.commit()
        print(f"\n📧 New OTP for {email}: {otp}\n")
        send_otp_email(email, user.name, otp)
        flash('New OTP sent! Check your email (or console in demo mode).', 'success')

    return redirect(url_for('auth.verify_otp'))


# ============================================
# LOGIN ROUTE
# ============================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)

        if not email or not password:
            flash('Email and password are required!', 'error')
            return render_template('auth/login.html')

        # Database mein user dhundo
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with this email!', 'error')
            return render_template('auth/login.html')

        # Password check karo
        # check_password_hash: stored hash aur entered password compare karta hai
        if not check_password_hash(user.password, password):
            flash('Incorrect password!', 'error')
            return render_template('auth/login.html')

        if not user.is_verified:
            session['verify_email'] = email
            flash('Please verify your email first!', 'warning')
            return redirect(url_for('auth.verify_otp'))

        # Login karo
        login_user(user, remember=bool(remember))
        flash(f'Welcome back, {user.name}! ✈️', 'success')

        # Next page pe redirect karo (agar koi tha to)
        next_page = request.args.get('next')
        return redirect(next_page if next_page else url_for('dashboard.dashboard'))

    return render_template('auth/login.html')


# ============================================
# LOGOUT ROUTE
# ============================================
@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    name = current_user.name
    logout_user()
    flash(f'Goodbye, {name}! Have a safe flight! ✈️', 'info')
    return redirect(url_for('index'))


# ============================================
# HELPER FUNCTION: Send OTP Email
# ============================================
def send_otp_email(email, name, otp):
    """
    OTP email bhejta hai
    Development mein: sirf console pe print karta hai
    Production mein: real email bhejta hai Flask-Mail se
    """
    try:
        from flask_mail import Message
        from flask import current_app
        mail_username = current_app.config.get('MAIL_USERNAME', '')

        # Agar dummy email hai to skip karo
        if 'your_email' in mail_username or not mail_username:
            print(f"📧 [DEMO MODE] OTP Email to {email}: {otp}")
            return

        from app import mail
        msg = Message(
            subject='SkyBook - Email Verification OTP',
            recipients=[email],
            html=f"""
            <h2>Welcome to SkyBook! ✈️</h2>
            <p>Hello {name},</p>
            <p>Your OTP for email verification is:</p>
            <h1 style="color:#2563eb;letter-spacing:5px">{otp}</h1>
            <p>This OTP expires in 10 minutes.</p>
            <p>If you did not signup, ignore this email.</p>
            """
        )
        mail.send(msg)
    except Exception as e:
        print(f"📧 Email Error (Demo Mode - OTP printed above): {e}")
