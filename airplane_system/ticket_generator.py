# ============================================
# ticket_generator.py
# ============================================
# Concept: reportlab = Python se PDF banana
# qrcode   = QR image banana
# io.BytesIO = Memory mein file rakhna (disk pe save kiye baghair)
#
# Flow:
# 1. Booking data lo
# 2. QR code banao (booking URL encode karo)
# 3. PDF banao (reportlab canvas pe draw karo)
# 4. PDF bytes return karo → email attachment ya download
# ============================================

import io
import qrcode
import base64
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage


# ── Brand colours ──────────────────────────
NAVY   = colors.HexColor('#0f172a')
BLUE   = colors.HexColor('#1d4ed8')
LTBLUE = colors.HexColor('#dbeafe')
WHITE  = colors.white
GRAY   = colors.HexColor('#64748b')
LGRAY  = colors.HexColor('#f1f5f9')
GREEN  = colors.HexColor('#16a34a')
RED    = colors.HexColor('#dc2626')
AMBER  = colors.HexColor('#d97706')

# Airline brand colours
AIRLINE_COLORS = {
    'PK': colors.HexColor('#006633'),
    'EK': colors.HexColor('#cc0001'),
    'QR': colors.HexColor('#5c0632'),
    'G9': colors.HexColor('#e31837'),
    'ER': colors.HexColor('#002b5c'),
}


def make_qr_bytes(booking) -> bytes:
    """
    QR code image bytes return karta hai.
    QR mein booking URL encode hoti hai taake scan karne par
    directly ticket page khule.
    """
    qr_data = (
        f"SKYBOOK TICKET\n"
        f"ID: {booking.booking_id}\n"
        f"Flight: {booking.flight.flight_number}\n"
        f"{booking.flight.from_city} -> {booking.flight.to_city}\n"
        f"Date: {booking.travel_date}\n"
        f"Passenger: {booking.passenger_name}\n"
        f"Status: {booking.payment_status}\n"
        f"Verify: https://skybook.com/verify/{booking.booking_id}"
    )
    qr = qrcode.QRCode(version=2, box_size=6, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def make_qr_base64(booking) -> str:
    """QR code ka base64 string — HTML mein <img src="data:..."> ke liye"""
    return base64.b64encode(make_qr_bytes(booking)).decode('utf-8')


def _status_color(payment_status: str):
    return {
        'Paid':                 GREEN,
        'Refunded':             GRAY,
        'Partially_Refunded':   AMBER,
        'Pending':              AMBER,
        'Failed':               RED,
    }.get(payment_status, GRAY)


def _booking_status_color(status: str):
    return GREEN if status == 'Confirmed' else RED


def generate_ticket_pdf(booking) -> bytes:
    """
    Main function — ek booking object lo, PDF bytes wapis do.

    reportlab canvas logic:
    - Canvas ka origin bottom-left hota hai (0,0)
    - y coordinate upar jaata hai
    - drawString(x, y, text) — x,y se text likhta hai
    - setFillColor → text/shape ka colour
    - rect(x, y, width, height) — box draw karta hai
    """
    buf = io.BytesIO()
    W, H = A4                          # 595 x 842 pts
    c = canvas.Canvas(buf, pagesize=A4)

    # ── 1. DARK HEADER BAND ───────────────────
    c.setFillColor(NAVY)
    c.rect(0, H - 90*mm, W, 90*mm, fill=1, stroke=0)

    # Airline coloured left strip
    ac = AIRLINE_COLORS.get(booking.flight.airline_code, BLUE)
    c.setFillColor(ac)
    c.rect(0, H - 90*mm, 8*mm, 90*mm, fill=1, stroke=0)

    # Brand name
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(15*mm, H - 22*mm, "SKY")
    c.setFillColor(colors.HexColor('#60a5fa'))
    c.drawString(37*mm, H - 22*mm, "BOOK")

    # Tagline
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont("Helvetica", 8)
    c.drawString(15*mm, H - 29*mm, "Electronic Ticket  |  skybook.com")

    # Booking ID badge
    c.setFillColor(BLUE)
    c.roundRect(W - 75*mm, H - 28*mm, 62*mm, 12*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(W - 44*mm, H - 23*mm, booking.booking_id)

    # ── 2. ROUTE SECTION ─────────────────────
    y_route = H - 68*mm

    # From
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 36)
    c.drawString(15*mm, y_route, booking.flight.from_airport)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.drawString(15*mm, y_route - 7*mm, booking.flight.from_city)

    # Arrow + duration
    cx = W / 2
    c.setStrokeColor(colors.HexColor('#334155'))
    c.setLineWidth(1)
    c.line(65*mm, y_route - 1*mm, cx - 18*mm, y_route - 1*mm)
    c.setFillColor(colors.HexColor('#60a5fa'))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(cx, y_route, "✈")
    c.line(cx + 18*mm, y_route - 1*mm, W - 65*mm, y_route - 1*mm)
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont("Helvetica", 8)
    c.drawCentredString(cx, y_route - 7*mm, booking.flight.duration + "  •  Direct")

    # To
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 36)
    to_w = c.stringWidth(booking.flight.to_airport, "Helvetica-Bold", 36)
    c.drawString(W - 15*mm - to_w, y_route, booking.flight.to_airport)
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor('#94a3b8'))
    city_w = c.stringWidth(booking.flight.to_city, "Helvetica", 9)
    c.drawString(W - 15*mm - city_w, y_route - 7*mm, booking.flight.to_city)

    # ── 3. DETAILS GRID ──────────────────────
    y_grid = H - 105*mm
    details = [
        ("Flight", booking.flight.flight_number),
        ("Airline", booking.flight.airline),
        ("Departure", booking.flight.departure_time),
        ("Arrival", booking.flight.arrival_time),
        ("Travel Date", booking.travel_date.strftime('%d %B %Y')),
        ("Passenger", booking.passenger_name),
        ("Class", booking.seat_class),
        ("Passengers", str(booking.passengers)),
        ("Aircraft", booking.flight.aircraft_type),
        ("Contact", booking.passenger_email),
    ]

    # Light background
    c.setFillColor(LGRAY)
    c.roundRect(10*mm, y_grid - 62*mm, W - 20*mm, 64*mm, 3*mm, fill=1, stroke=0)

    col_w = (W - 20*mm) / 2
    for i, (label, value) in enumerate(details):
        col = i % 2
        row = i // 2
        x = 14*mm + col * col_w
        y = y_grid - 10*mm - row * 11*mm
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 7.5)
        c.drawString(x, y, label.upper())
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(x, y - 5.5*mm, value)

    # ── 4. TEAR LINE ─────────────────────────
    y_tear = y_grid - 72*mm
    c.setStrokeColor(colors.HexColor('#cbd5e1'))
    c.setDash(4, 4)
    c.line(15*mm, y_tear, W - 15*mm, y_tear)
    c.setDash()
    # Circles at ends
    c.setFillColor(colors.HexColor('#e2e8f0'))
    c.circle(10*mm, y_tear, 5*mm, fill=1, stroke=0)
    c.circle(W - 10*mm, y_tear, 5*mm, fill=1, stroke=0)

    # ── 5. BOTTOM SECTION ────────────────────
    y_bot = y_tear - 8*mm

    # Payment status badge
    pay_col = _status_color(booking.payment_status)
    c.setFillColor(pay_col)
    c.roundRect(14*mm, y_bot - 12*mm, 55*mm, 10*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(41.5*mm, y_bot - 8*mm,
                        f"PAYMENT: {booking.payment_status.upper()}")

    # Booking status badge
    bk_col = _booking_status_color(booking.status)
    c.setFillColor(bk_col)
    c.roundRect(74*mm, y_bot - 12*mm, 45*mm, 10*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(96.5*mm, y_bot - 8*mm,
                        f"STATUS: {booking.status.upper()}")

    # Refund info (if any)
    if booking.refund_amount and booking.refund_amount > 0:
        c.setFillColor(AMBER)
        c.roundRect(124*mm, y_bot - 12*mm, 65*mm, 10*mm, 2*mm, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(156.5*mm, y_bot - 8*mm,
                            f"REFUND: PKR {booking.refund_amount:,.0f}")

    # Total amount
    c.setFillColor(NAVY)
    c.setFont("Helvetica", 8)
    c.drawString(14*mm, y_bot - 20*mm, "Total Amount Paid:")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(BLUE)
    c.drawString(14*mm, y_bot - 28*mm, f"PKR {booking.total_price:,.0f}")

    # Payment method
    if booking.payment_method:
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 8)
        c.drawString(14*mm, y_bot - 35*mm,
                     f"Paid via: {booking.payment_method.title()}")

    # Booking date
    c.setFont("Helvetica", 7.5)
    c.drawString(14*mm, y_bot - 42*mm,
                 f"Booked: {booking.created_at.strftime('%d %b %Y %H:%M') if booking.created_at else 'N/A'}")

    # ── 6. QR CODE ───────────────────────────
    qr_bytes = make_qr_bytes(booking)
    qr_img   = ImageReader(io.BytesIO(qr_bytes))
    qr_size  = 38*mm
    qr_x     = W - 14*mm - qr_size
    qr_y     = y_bot - 45*mm
    c.drawImage(qr_img, qr_x, qr_y, qr_size, qr_size)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7)
    c.drawCentredString(qr_x + qr_size / 2, qr_y - 4*mm, "Scan to verify ticket")

    # ── 7. CANCELLATION POLICY BOX ───────────
    y_policy = qr_y - 12*mm
    c.setFillColor(colors.HexColor('#fef9c3'))
    c.roundRect(14*mm, y_policy - 22*mm, W - 28*mm, 24*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#854d0e'))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(18*mm, y_policy - 6*mm, "Cancellation Policy:")
    c.setFont("Helvetica", 7.5)
    c.drawString(18*mm, y_policy - 12*mm,
                 "Within 5 hours of booking: 10% fee deducted, 90% refunded to original payment method.")
    c.drawString(18*mm, y_policy - 18*mm,
                 "After 5 hours: 30% fee deducted, 70% refunded. Refunds processed within 5-7 business days.")

    # ── 8. FOOTER ────────────────────────────
    c.setFillColor(NAVY)
    c.rect(0, 0, W, 12*mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#94a3b8'))
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 4.5*mm,
                        "SkyBook Airlines  •  support@skybook.com  •  +92-21-111-SKY-FLY  •  skybook.com")

    c.save()
    return buf.getvalue()
