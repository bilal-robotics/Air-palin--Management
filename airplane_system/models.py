# ============================================
# models.py - Database Tables (Models)
# ============================================
# Concept: SQLAlchemy is an ORM (Object-Relational Mapper)
# ORM matlab: Python classes = Database Tables
# Ek class ka ek object = Database ki ek row
# Example: User(name="Ali") = users table mein ek row
# ============================================

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import random
import string

# db object - yeh SQLAlchemy ka core object hai
# Is object ke through hum database se baat karte hain
db = SQLAlchemy()


# ============================================
# USER MODEL
# ============================================
class User(UserMixin, db.Model):
    """
    UserMixin: Flask-Login ke liye required methods automatically add karta hai
    db.Model: Batata hai ke yeh ek database table hai
    """
    __tablename__ = 'users'  # Database mein table ka naam

    id = db.Column(db.Integer, primary_key=True)  # Auto-increment ID
    name = db.Column(db.String(100), nullable=False)  # nullable=False = required field
    email = db.Column(db.String(120), unique=True, nullable=False)  # unique = duplicate nahi
    password = db.Column(db.String(256), nullable=False)  # Hashed password store hoga
    is_verified = db.Column(db.Boolean, default=False)  # Email verified hai ya nahi
    otp = db.Column(db.String(6), nullable=True)  # 6 digit OTP
    otp_created_at = db.Column(db.DateTime, nullable=True)  # OTP kab banaya
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Account kab bana
    is_admin = db.Column(db.Boolean, default=False)  # Admin hai ya normal user

    # Relationship: Ek user ke multiple bookings ho sakti hain
    # backref='user' matlab: booking.user se user object milega
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')

    def generate_otp(self):
        """6 digit random OTP generate karta hai"""
        self.otp = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = datetime.utcnow()
        return self.otp

    def __repr__(self):
        return f'<User {self.email}>'


# ============================================
# FLIGHT MODEL
# ============================================
class Flight(db.Model):
    """
    Flight table - sab available flights yahan store hongi
    """
    __tablename__ = 'flights'

    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), unique=True, nullable=False)  # e.g., PK-301
    airline = db.Column(db.String(100), nullable=False)  # e.g., PIA, Emirates
    airline_code = db.Column(db.String(10), nullable=False)  # e.g., PK, EK
    from_city = db.Column(db.String(100), nullable=False)  # Departure city
    to_city = db.Column(db.String(100), nullable=False)    # Destination city
    from_airport = db.Column(db.String(10), nullable=False)  # Airport code e.g., KHI
    to_airport = db.Column(db.String(10), nullable=False)    # Airport code e.g., LHE
    departure_time = db.Column(db.String(10), nullable=False)  # e.g., "08:30"
    arrival_time = db.Column(db.String(10), nullable=False)    # e.g., "10:45"
    duration = db.Column(db.String(20), nullable=False)  # e.g., "2h 15m"
    price = db.Column(db.Float, nullable=False)          # Price per seat (PKR)
    total_seats = db.Column(db.Integer, default=150)     # Total seats
    available_seats = db.Column(db.Integer, default=150) # Available seats
    aircraft_type = db.Column(db.String(50), default='Boeing 737')
    is_active = db.Column(db.Boolean, default=True)      # Flight active hai ya nahi
    days_of_week = db.Column(db.String(50), default='Mon,Tue,Wed,Thu,Fri,Sat,Sun')

    # Relationship with bookings
    bookings = db.relationship('Booking', backref='flight', lazy=True)

    def __repr__(self):
        return f'<Flight {self.flight_number}: {self.from_city} → {self.to_city}>'


# ============================================
# BOOKING MODEL
# ============================================
class Booking(db.Model):
    """
    Booking table - jab user ticket book kare tab yahan record save hoga
    user_id aur flight_id = Foreign Keys (doosre tables se link)
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True, nullable=False)  # e.g., SKY-2024-XXXXX
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)   # users table se link
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'), nullable=False) # flights table se link
    travel_date = db.Column(db.Date, nullable=False)        # Jis din travel karna hai
    passengers = db.Column(db.Integer, nullable=False, default=1)  # Kitne passengers
    seat_class = db.Column(db.String(20), default='Economy')  # Economy/Business/First
    total_price = db.Column(db.Float, nullable=False)        # Total payment
    status = db.Column(db.String(20), default='Confirmed')   # Confirmed/Cancelled/Pending
    passenger_name = db.Column(db.String(100), nullable=False)  # Main passenger name
    passenger_email = db.Column(db.String(120), nullable=False)  # Contact email
    passenger_phone = db.Column(db.String(20), nullable=True)    # Contact phone
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Booking kab ki

    # Payment fields
    payment_status   = db.Column(db.String(20), default='Pending')
    # Pending / Paid / Refunded / Partially_Refunded / Failed
    payment_method   = db.Column(db.String(30), nullable=True)
    # stripe / jazzcash / easypaisa / paypal / cash
    payment_id       = db.Column(db.String(200), nullable=True)   # Gateway transaction ID
    refund_amount    = db.Column(db.Float, default=0.0)
    refund_status    = db.Column(db.String(20), nullable=True)     # Pending / Done
    refund_requested_at = db.Column(db.DateTime, nullable=True)
    pdf_generated    = db.Column(db.Boolean, default=False)
    ticket_qr_code   = db.Column(db.Text, nullable=True)          # base64 QR image

    def generate_booking_id(self):
        """Unique booking ID generate karta hai"""
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(random.choices(chars, k=6))
        self.booking_id = f'SKY-{datetime.utcnow().year}-{random_part}'
        return self.booking_id

    def calculate_refund(self):
        """
        Refund calculate karta hai cancellation policy ke mutabiq:
        - 5 hours se pehle cancel: 10% fee, 90% wapis
        - 5 hours ke baad cancel:  30% fee, 70% wapis
        Returns: (refund_amount, fee_percent, refund_percent)
        """
        import os
        from datetime import timedelta
        threshold_hours = int(os.environ.get('LATE_CANCEL_THRESHOLD_HOURS', 5))
        if self.created_at:
            time_since_booking = datetime.utcnow() - self.created_at
            if time_since_booking <= timedelta(hours=threshold_hours):
                fee_pct = int(os.environ.get('EARLY_CANCEL_FEE_PERCENT', 10))
            else:
                fee_pct = int(os.environ.get('LATE_CANCEL_FEE_PERCENT', 30))
        else:
            fee_pct = 30
        refund_pct = 100 - fee_pct
        refund_amt = round(self.total_price * refund_pct / 100, 2)
        return refund_amt, fee_pct, refund_pct

    def __repr__(self):
        return f'<Booking {self.booking_id}>'
