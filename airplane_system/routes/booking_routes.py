# ============================================
# routes/booking_routes.py - Ticket Booking
# ============================================

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, Flight, Booking
from datetime import datetime, date

booking_bp = Blueprint('bookings', __name__)


# ============================================
# BOOK FLIGHT PAGE
# ============================================
@booking_bp.route('/book/<int:flight_id>', methods=['GET', 'POST'])
@login_required  # Sirf logged-in users book kar sakte hain
def book_flight(flight_id):
    """
    GET: Booking form dikhao
    POST: Booking save karo
    """
    flight = Flight.query.get_or_404(flight_id)
    travel_date_str = request.args.get('date', '')
    passengers = request.args.get('passengers', 1, type=int)

    if request.method == 'POST':
        # Form data lo
        travel_date_str = request.form.get('travel_date')
        passengers = request.form.get('passengers', 1, type=int)
        seat_class = request.form.get('seat_class', 'Economy')
        passenger_name = request.form.get('passenger_name', '').strip()
        passenger_phone = request.form.get('passenger_phone', '').strip()

        # Validation
        if not travel_date_str or not passenger_name:
            flash('Please fill all required fields!', 'error')
            return render_template('bookings/book.html', flight=flight,
                                   travel_date=travel_date_str, passengers=passengers)

        # Date parse karo
        try:
            travel_date = datetime.strptime(travel_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format!', 'error')
            return render_template('bookings/book.html', flight=flight,
                                   travel_date=travel_date_str, passengers=passengers)

        # Past date check
        if travel_date < date.today():
            flash('Travel date cannot be in the past!', 'error')
            return render_template('bookings/book.html', flight=flight,
                                   travel_date=travel_date_str, passengers=passengers)

        # Seats available check
        if flight.available_seats < passengers:
            flash(f'Only {flight.available_seats} seats available!', 'error')
            return render_template('bookings/book.html', flight=flight,
                                   travel_date=travel_date_str, passengers=passengers)

        # Price calculate karo
        class_multiplier = {'Economy': 1.0, 'Business': 2.5, 'First': 4.0}
        multiplier = class_multiplier.get(seat_class, 1.0)
        total_price = flight.price * passengers * multiplier

        # Booking object banao
        new_booking = Booking(
            user_id=current_user.id,
            flight_id=flight.id,
            travel_date=travel_date,
            passengers=passengers,
            seat_class=seat_class,
            total_price=total_price,
            passenger_name=passenger_name,
            passenger_email=current_user.email,
            passenger_phone=passenger_phone,
            status='Confirmed'
        )

        # Booking ID generate karo
        new_booking.generate_booking_id()

        # Available seats update karo
        flight.available_seats -= passengers

        # Database mein save karo
        db.session.add(new_booking)
        db.session.commit()

        flash(f'Booking created! ID: {new_booking.booking_id}. Please complete payment to confirm.', 'success')
        return redirect(url_for('payment.payment_page', booking_id=new_booking.id))

    return render_template('bookings/book.html',
                           flight=flight,
                           travel_date=travel_date_str,
                           passengers=passengers,
                           today=date.today().isoformat())


# ============================================
# BOOKING CONFIRMATION PAGE
# ============================================
@booking_bp.route('/booking/confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    """Booking success page"""
    booking = Booking.query.get_or_404(booking_id)

    # Security: sirf apni booking dekh sako
    if booking.user_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard.dashboard'))

    return render_template('bookings/confirmation.html', booking=booking)


# ============================================
# MY BOOKINGS PAGE
# ============================================
@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    """User ki saari bookings"""
    # Current user ki bookings - newest pehle
    bookings = Booking.query.filter_by(user_id=current_user.id)\
                            .order_by(Booking.created_at.desc()).all()

    return render_template('bookings/my_bookings.html', bookings=bookings)


# ============================================
# BOOKING DETAIL PAGE
# ============================================
@booking_bp.route('/booking/<int:booking_id>')
@login_required
def booking_detail(booking_id):
    """Single booking ki detail"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('bookings.my_bookings'))

    return render_template('bookings/detail.html', booking=booking)


# ============================================
# CANCEL BOOKING
# ============================================
@booking_bp.route('/booking/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    """Booking cancel karta hai"""
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('bookings.my_bookings'))

    if booking.status == 'Cancelled':
        flash('Booking is already cancelled!', 'warning')
        return redirect(url_for('bookings.my_bookings'))

    # Travel date check - 24 hours pehle cancel ho sakti hai
    if booking.travel_date <= date.today():
        flash('Cannot cancel booking for today or past dates!', 'error')
        return redirect(url_for('bookings.my_bookings'))

    # Booking cancel karo
    booking.status = 'Cancelled'

    # Seats wapis karo
    booking.flight.available_seats += booking.passengers

    db.session.commit()
    flash(f'Booking {booking.booking_id} cancelled successfully!', 'success')
    return redirect(url_for('bookings.my_bookings'))
