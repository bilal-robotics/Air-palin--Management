# ============================================
# routes/admin_routes.py - Admin Panel
# ============================================

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Flight, Booking
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Custom decorator: Sirf admins access kar sakein"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required!', 'error')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    """Admin main page"""
    total_users = User.query.count()
    total_flights = Flight.query.count()
    total_bookings = Booking.query.count()
    confirmed = Booking.query.filter_by(status='Confirmed').count()
    cancelled = Booking.query.filter_by(status='Cancelled').count()

    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(10).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    revenue = db.session.query(
        db.func.sum(Booking.total_price)
    ).filter(Booking.status == 'Confirmed').scalar() or 0

    return render_template('admin/dashboard.html',
        total_users=total_users, total_flights=total_flights,
        total_bookings=total_bookings, confirmed=confirmed,
        cancelled=cancelled, recent_bookings=recent_bookings,
        recent_users=recent_users, revenue=revenue)


@admin_bp.route('/flights')
@login_required
@admin_required
def admin_flights():
    flights = Flight.query.all()
    return render_template('admin/flights.html', flights=flights)


@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/bookings')
@login_required
@admin_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)


@admin_bp.route('/flight/toggle/<int:flight_id>', methods=['POST'])
@login_required
@admin_required
def toggle_flight(flight_id):
    flight = Flight.query.get_or_404(flight_id)
    flight.is_active = not flight.is_active
    db.session.commit()
    status = "activated" if flight.is_active else "deactivated"
    flash(f'Flight {flight.flight_number} {status}!', 'success')
    return redirect(url_for('admin.admin_flights'))
