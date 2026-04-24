# ============================================
# app.py - Flask Application Entry Point
# ============================================
# Concept: app.py Flask ka "brain" hai
# Yahan sab kuch initialize hota hai:
# 1. Flask app create hoti hai
# 2. Database connect hoti hai
# 3. Email system setup hota hai
# 4. Routes register hote hain
# 5. Dummy data insert hoti hai
# ============================================

import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from dotenv import load_dotenv
from models import db, User, Flight, Booking
from datetime import datetime

# .env file se environment variables load karo
# Concept: .env file mein sensitive data hota hai (passwords, API keys)
# os.environ se variables milte hain
load_dotenv()

# ============================================
# Flask App Initialize
# ============================================
app = Flask(__name__)

# Configuration settings
# SECRET_KEY: Session data encrypt karne ke liye use hoti hai
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database path: project folder mein database.db file banega
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Memory save karta hai

# Email Configuration (Flask-Mail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your_email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your_app_password')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your_email@gmail.com')

# ============================================
# Initialize Extensions
# ============================================
db.init_app(app)       # Database app se connect karo
mail = Mail(app)       # Email system initialize karo

# Flask-Login Setup
# LoginManager: User session manage karta hai (login/logout)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'  # Agar user login nahi to yahan redirect karo
login_manager.login_message = 'Please login to access this page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login har request pe yeh function call karta hai
    Session mein user_id hoti hai, is se User object milta hai
    """
    return User.query.get(int(user_id))

# ============================================
# Register Blueprints (Route Files)
# ============================================
# Blueprint = Routes ka group - alag files mein organize karte hain
from routes.auth_routes import auth_bp
from routes.flight_routes import flight_bp
from routes.booking_routes import booking_bp
from routes.dashboard_routes import dashboard_bp
from routes.admin_routes import admin_bp
from routes.payment_routes import payment_bp

app.register_blueprint(auth_bp)       # /login, /signup, /logout
app.register_blueprint(flight_bp)     # /flights, /search
app.register_blueprint(booking_bp)    # /book, /bookings, /cancel
app.register_blueprint(dashboard_bp)  # /dashboard
app.register_blueprint(admin_bp)      # /admin
app.register_blueprint(payment_bp)    # /payment, /ticket, /verify

# ============================================
# Database Initialization & Seed Data
# ============================================
def seed_flights():
    """
    Dummy flight data insert karta hai agar koi flight nahi hai
    Seed data = initial/test data
    """
    if Flight.query.count() > 0:
        return  # Already data hai, skip karo

    flights_data = [
        # PIA Flights
        {
            'flight_number': 'PK-301', 'airline': 'Pakistan International Airlines', 'airline_code': 'PK',
            'from_city': 'Karachi', 'to_city': 'Lahore', 'from_airport': 'KHI', 'to_airport': 'LHE',
            'departure_time': '08:00', 'arrival_time': '09:30', 'duration': '1h 30m',
            'price': 12500, 'total_seats': 150, 'available_seats': 120, 'aircraft_type': 'Boeing 737'
        },
        {
            'flight_number': 'PK-302', 'airline': 'Pakistan International Airlines', 'airline_code': 'PK',
            'from_city': 'Lahore', 'to_city': 'Karachi', 'from_airport': 'LHE', 'to_airport': 'KHI',
            'departure_time': '14:00', 'arrival_time': '15:30', 'duration': '1h 30m',
            'price': 12500, 'total_seats': 150, 'available_seats': 98, 'aircraft_type': 'Boeing 737'
        },
        {
            'flight_number': 'PK-201', 'airline': 'Pakistan International Airlines', 'airline_code': 'PK',
            'from_city': 'Karachi', 'to_city': 'Islamabad', 'from_airport': 'KHI', 'to_airport': 'ISB',
            'departure_time': '10:30', 'arrival_time': '12:15', 'duration': '1h 45m',
            'price': 14000, 'total_seats': 150, 'available_seats': 75, 'aircraft_type': 'Airbus A320'
        },
        {
            'flight_number': 'PK-401', 'airline': 'Pakistan International Airlines', 'airline_code': 'PK',
            'from_city': 'Karachi', 'to_city': 'Dubai', 'from_airport': 'KHI', 'to_airport': 'DXB',
            'departure_time': '02:30', 'arrival_time': '04:30', 'duration': '2h 00m',
            'price': 45000, 'total_seats': 200, 'available_seats': 145, 'aircraft_type': 'Boeing 777'
        },
        # Emirates Flights
        {
            'flight_number': 'EK-601', 'airline': 'Emirates', 'airline_code': 'EK',
            'from_city': 'Karachi', 'to_city': 'Dubai', 'from_airport': 'KHI', 'to_airport': 'DXB',
            'departure_time': '09:15', 'arrival_time': '11:15', 'duration': '2h 00m',
            'price': 62000, 'total_seats': 350, 'available_seats': 230, 'aircraft_type': 'Airbus A380'
        },
        {
            'flight_number': 'EK-602', 'airline': 'Emirates', 'airline_code': 'EK',
            'from_city': 'Lahore', 'to_city': 'Dubai', 'from_airport': 'LHE', 'to_airport': 'DXB',
            'departure_time': '11:30', 'arrival_time': '13:30', 'duration': '2h 00m',
            'price': 58000, 'total_seats': 350, 'available_seats': 189, 'aircraft_type': 'Boeing 777'
        },
        {
            'flight_number': 'EK-701', 'airline': 'Emirates', 'airline_code': 'EK',
            'from_city': 'Karachi', 'to_city': 'London', 'from_airport': 'KHI', 'to_airport': 'LHR',
            'departure_time': '20:45', 'arrival_time': '06:30', 'duration': '9h 45m',
            'price': 185000, 'total_seats': 350, 'available_seats': 67, 'aircraft_type': 'Airbus A380'
        },
        # Qatar Airways
        {
            'flight_number': 'QR-501', 'airline': 'Qatar Airways', 'airline_code': 'QR',
            'from_city': 'Karachi', 'to_city': 'Doha', 'from_airport': 'KHI', 'to_airport': 'DOH',
            'departure_time': '03:45', 'arrival_time': '05:45', 'duration': '2h 00m',
            'price': 55000, 'total_seats': 300, 'available_seats': 210, 'aircraft_type': 'Boeing 787'
        },
        {
            'flight_number': 'QR-502', 'airline': 'Qatar Airways', 'airline_code': 'QR',
            'from_city': 'Islamabad', 'to_city': 'Doha', 'from_airport': 'ISB', 'to_airport': 'DOH',
            'departure_time': '07:20', 'arrival_time': '09:20', 'duration': '2h 00m',
            'price': 52000, 'total_seats': 300, 'available_seats': 178, 'aircraft_type': 'Airbus A350'
        },
        {
            'flight_number': 'QR-801', 'airline': 'Qatar Airways', 'airline_code': 'QR',
            'from_city': 'Karachi', 'to_city': 'New York', 'from_airport': 'KHI', 'to_airport': 'JFK',
            'departure_time': '22:00', 'arrival_time': '10:30', 'duration': '16h 30m',
            'price': 280000, 'total_seats': 300, 'available_seats': 45, 'aircraft_type': 'Boeing 777X'
        },
        # Air Arabia
        {
            'flight_number': 'G9-201', 'airline': 'Air Arabia', 'airline_code': 'G9',
            'from_city': 'Karachi', 'to_city': 'Sharjah', 'from_airport': 'KHI', 'to_airport': 'SHJ',
            'departure_time': '06:30', 'arrival_time': '08:30', 'duration': '2h 00m',
            'price': 35000, 'total_seats': 180, 'available_seats': 156, 'aircraft_type': 'Airbus A320'
        },
        # Serene Air
        {
            'flight_number': 'ER-101', 'airline': 'Serene Air', 'airline_code': 'ER',
            'from_city': 'Karachi', 'to_city': 'Lahore', 'from_airport': 'KHI', 'to_airport': 'LHE',
            'departure_time': '16:00', 'arrival_time': '17:30', 'duration': '1h 30m',
            'price': 11000, 'total_seats': 120, 'available_seats': 88, 'aircraft_type': 'Boeing 737'
        },
        {
            'flight_number': 'ER-102', 'airline': 'Serene Air', 'airline_code': 'ER',
            'from_city': 'Lahore', 'to_city': 'Islamabad', 'from_airport': 'LHE', 'to_airport': 'ISB',
            'departure_time': '19:00', 'arrival_time': '20:00', 'duration': '1h 00m',
            'price': 8500, 'total_seats': 120, 'available_seats': 102, 'aircraft_type': 'Boeing 737'
        },
    ]

    for fd in flights_data:
        flight = Flight(**fd)
        db.session.add(flight)

    db.session.commit()
    print(f"✅ {len(flights_data)} flights added to database")


def create_admin():
    """Default admin account banata hai"""
    from werkzeug.security import generate_password_hash
    admin = User.query.filter_by(email='admin@skybook.com').first()
    if not admin:
        admin = User(
            name='Sky Admin',
            email='admin@skybook.com',
            password=generate_password_hash('admin123'),
            is_verified=True,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin account created: admin@skybook.com / admin123")


# ============================================
# Home Route
# ============================================
from flask import render_template

@app.route('/')
def index():
    """Home page - sabse pehle yahi page load hoga"""
    return render_template('index.html')


# ============================================
# Run Application
# ============================================
if __name__ == '__main__':
    with app.app_context():
        # Tables create karo agar exist nahi karte
        db.create_all()
        print("✅ Database tables created")
        # Dummy data insert karo
        seed_flights()
        create_admin()

    print("\n🛫 SkyBook - Airplane Management System")
    print("=" * 45)
    print("🌐 URL: http://127.0.0.1:5000")
    print("👤 Admin: admin@skybook.com / admin123")
    print("=" * 45)
    app.run(debug=True, host='0.0.0.0', port=5000)
