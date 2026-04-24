# ============================================
# routes/dashboard_routes.py - User Dashboard
# ============================================

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, Booking, Flight
from datetime import date, datetime

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """User ka main dashboard"""

    # Recent 5 bookings
    recent_bookings = Booking.query.filter_by(user_id=current_user.id)\
                                   .order_by(Booking.created_at.desc())\
                                   .limit(5).all()

    # Stats calculate karo
    total_bookings = Booking.query.filter_by(user_id=current_user.id).count()
    confirmed_bookings = Booking.query.filter_by(
        user_id=current_user.id, status='Confirmed').count()
    cancelled_bookings = Booking.query.filter_by(
        user_id=current_user.id, status='Cancelled').count()

    # Upcoming travel
    upcoming_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.travel_date >= date.today(),
        Booking.status == 'Confirmed'
    ).order_by(Booking.travel_date).limit(3).all()

    # Total spend
    total_spent = db.session.query(
        db.func.sum(Booking.total_price)
    ).filter(
        Booking.user_id == current_user.id,
        Booking.status == 'Confirmed'
    ).scalar() or 0

    return render_template(
        'dashboard/dashboard.html',
        recent_bookings=recent_bookings,
        total_bookings=total_bookings,
        confirmed_bookings=confirmed_bookings,
        cancelled_bookings=cancelled_bookings,
        upcoming_bookings=upcoming_bookings,
        total_spent=total_spent,
        today=date.today()
    )
