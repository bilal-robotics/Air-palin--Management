# ============================================
# routes/payment_routes.py
# ============================================
# Yahan 4 payment methods hain:
# 1. JazzCash   — Pakistan local
# 2. Easypaisa  — Pakistan local
# 3. Stripe     — International cards
# 4. PayPal     — International wallet
# 5. Cash       — Manual (admin approve karta hai)
#
# Concept: Har gateway ka alag flow hota hai lekin
# sab ki end result same hai: booking.payment_status = 'Paid'
# ============================================

import os, hashlib, hmac, json, stripe
from datetime import datetime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, send_file, current_app)
from flask_login import login_required, current_user
from models import db, Booking
from ticket_generator import generate_ticket_pdf, make_qr_base64
import io

payment_bp = Blueprint('payment', __name__)

# ── Load Stripe key when module loads ────────────────────────────────────────
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')


# ════════════════════════════════════════════════════════════════════════════
# PAYMENT SELECTION PAGE
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/<int:booking_id>')
@login_required
def payment_page(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard.dashboard'))
    if booking.payment_status == 'Paid':
        flash('This booking is already paid!', 'info')
        return redirect(url_for('payment.ticket_view', booking_id=booking.id))
    stripe_pk = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    paypal_client_id = os.environ.get('PAYPAL_CLIENT_ID', '')
    return render_template('payment/select.html',
                           booking=booking,
                           stripe_pk=stripe_pk,
                           paypal_client_id=paypal_client_id)


# ════════════════════════════════════════════════════════════════════════════
# STRIPE — International Cards
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/stripe/create-intent/<int:booking_id>', methods=['POST'])
@login_required
def stripe_create_intent(booking_id):
    """
    Stripe PaymentIntent banata hai.
    Concept: Intent = "main itna charge karna chahta hoon"
    Frontend JS is intent ko complete karta hai card details se.
    """
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    sk = os.environ.get('STRIPE_SECRET_KEY', '')
    if not sk or sk == 'sk_test_YOUR_STRIPE_SECRET_KEY':
        # Demo mode — fake a successful payment
        return jsonify({'demo': True,
                        'client_secret': 'demo_secret',
                        'amount': int(booking.total_price * 100)})
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(booking.total_price * 100),   # Stripe paise cents mein leta hai
            currency='pkr',
            metadata={'booking_id': str(booking.id),
                      'booking_ref': booking.booking_id}
        )
        return jsonify({'client_secret': intent.client_secret,
                        'amount': intent.amount})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@payment_bp.route('/payment/stripe/confirm/<int:booking_id>', methods=['POST'])
@login_required
def stripe_confirm(booking_id):
    """Stripe payment confirmed — booking update karo"""
    booking = Booking.query.get_or_404(booking_id)
    data = request.get_json() or {}
    payment_intent_id = data.get('payment_intent_id', 'STRIPE_DEMO')

    _mark_paid(booking, method='Stripe', payment_id=payment_intent_id)
    _send_ticket_email(booking)
    return jsonify({'success': True,
                    'redirect': url_for('payment.ticket_view', booking_id=booking.id)})


# ════════════════════════════════════════════════════════════════════════════
# JAZZCASH — Pakistan
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/jazzcash/<int:booking_id>', methods=['POST'])
@login_required
def jazzcash_pay(booking_id):
    """
    JazzCash redirect payment.
    Concept: Hum form data + hash bhejte hain JazzCash server ko.
    JazzCash payment lete hain aur hame callback deta hai.
    Hash = security signature (data tamper nahi hua proof)
    """
    booking = Booking.query.get_or_404(booking_id)
    merchant_id   = os.environ.get('JAZZCASH_MERCHANT_ID', 'DEMO_MERCHANT')
    password      = os.environ.get('JAZZCASH_PASSWORD', 'DEMO_PASS')
    salt          = os.environ.get('JAZZCASH_INTEGRITY_SALT', 'DEMO_SALT')
    is_sandbox    = os.environ.get('JAZZCASH_SANDBOX', 'True') == 'True'

    txn_ref = f"SKY{booking.booking_id.replace('-','')}"
    amount_str = str(int(booking.total_price * 100))   # JazzCash paisa (100x)
    txn_date = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    expiry    = datetime.utcnow().strftime('%Y%m%d') + '235959'

    callback_url = url_for('payment.jazzcash_callback', booking_id=booking_id,
                           _external=True)

    # Hash string banana (JazzCash documentation ke mutabiq)
    hash_str = (f"{salt}&{amount_str}&{expiry}&{merchant_id}"
                f"&{callback_url}&{txn_ref}&{txn_date}&PKR&MWALLET")
    secure_hash = hmac.new(salt.encode(), hash_str.encode(),
                           hashlib.sha256).hexdigest().upper()

    if is_sandbox:
        endpoint = "https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/"
    else:
        endpoint = "https://payments.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/"

    # Demo mode check
    if merchant_id == 'DEMO_MERCHANT':
        flash('JazzCash Demo Mode — simulating payment...', 'info')
        return redirect(url_for('payment.demo_success',
                                booking_id=booking_id, method='JazzCash'))

    return render_template('payment/jazzcash_redirect.html',
                           endpoint=endpoint,
                           merchant_id=merchant_id,
                           txn_ref=txn_ref,
                           amount=amount_str,
                           txn_date=txn_date,
                           expiry=expiry,
                           callback_url=callback_url,
                           secure_hash=secure_hash,
                           booking=booking)


@payment_bp.route('/payment/jazzcash/callback/<int:booking_id>', methods=['POST'])
def jazzcash_callback(booking_id):
    """JazzCash hame yahan callback deta hai"""
    booking = Booking.query.get_or_404(booking_id)
    response_code = request.form.get('pp_ResponseCode', '')
    txn_ref = request.form.get('pp_TxnRefNo', '')

    if response_code == '000':   # 000 = success JazzCash mein
        _mark_paid(booking, method='JazzCash', payment_id=txn_ref)
        _send_ticket_email(booking)
        flash('JazzCash payment successful!', 'success')
        return redirect(url_for('payment.ticket_view', booking_id=booking.id))
    else:
        booking.payment_status = 'Failed'
        db.session.commit()
        flash(f'JazzCash payment failed. Code: {response_code}', 'error')
        return redirect(url_for('payment.payment_page', booking_id=booking.id))


# ════════════════════════════════════════════════════════════════════════════
# EASYPAISA — Pakistan
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/easypaisa/<int:booking_id>', methods=['POST'])
@login_required
def easypaisa_pay(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    store_id = os.environ.get('EASYPAISA_STORE_ID', 'DEMO_STORE')

    if store_id == 'DEMO_STORE':
        flash('Easypaisa Demo Mode — simulating payment...', 'info')
        return redirect(url_for('payment.demo_success',
                                booking_id=booking_id, method='Easypaisa'))

    # Real Easypaisa integration
    hash_key    = os.environ.get('EASYPAISA_HASH_KEY', '')
    is_sandbox  = os.environ.get('EASYPAISA_SANDBOX', 'True') == 'True'
    order_id    = f"SKY{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    amount_str  = f"{booking.total_price:.2f}"
    callback    = url_for('payment.easypaisa_callback', booking_id=booking_id, _external=True)

    payload_str = (f"amount={amount_str}&"
                   f"orderRefNum={order_id}&"
                   f"paymentMethod=MA_PAYMENT&"
                   f"storeId={store_id}&"
                   f"mobileNum={booking.passenger_phone or '03001234567'}&"
                   f"postBackURL={callback}")

    ep_hash = hashlib.md5((hash_key + payload_str).encode()).hexdigest()

    if is_sandbox:
        endpoint = "https://easypay.easypaisa.com.pk/tpg/"
    else:
        endpoint = "https://easypay.easypaisa.com.pk/tpg/"

    return render_template('payment/easypaisa_redirect.html',
                           endpoint=endpoint,
                           store_id=store_id,
                           order_id=order_id,
                           amount=amount_str,
                           callback=callback,
                           ep_hash=ep_hash,
                           booking=booking)


@payment_bp.route('/payment/easypaisa/callback/<int:booking_id>', methods=['GET', 'POST'])
def easypaisa_callback(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    status = request.values.get('status', '')
    ref = request.values.get('transactionRefNum', 'EP_TXN')

    if status.lower() in ('paid', 'success', '1'):
        _mark_paid(booking, method='Easypaisa', payment_id=ref)
        _send_ticket_email(booking)
        flash('Easypaisa payment successful!', 'success')
        return redirect(url_for('payment.ticket_view', booking_id=booking.id))
    else:
        booking.payment_status = 'Failed'
        db.session.commit()
        flash('Easypaisa payment failed or cancelled.', 'error')
        return redirect(url_for('payment.payment_page', booking_id=booking.id))


# ════════════════════════════════════════════════════════════════════════════
# PAYPAL — International
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/paypal/create-order/<int:booking_id>', methods=['POST'])
@login_required
def paypal_create_order(booking_id):
    """
    PayPal order banao via REST API.
    Concept: PayPal ko batao "mujhe $X chahiye"
    PayPal JS SDK yeh complete karta hai browser mein.
    """
    booking = Booking.query.get_or_404(booking_id)
    client_id     = os.environ.get('PAYPAL_CLIENT_ID', '')
    client_secret = os.environ.get('PAYPAL_CLIENT_SECRET', '')
    is_sandbox    = os.environ.get('PAYPAL_SANDBOX', 'True') == 'True'

    if not client_id or client_id == 'YOUR_PAYPAL_CLIENT_ID':
        return jsonify({'demo': True, 'order_id': 'PAYPAL_DEMO_ORDER'})

    base = ("https://api-m.sandbox.paypal.com" if is_sandbox
            else "https://api-m.paypal.com")
    import requests as req

    # Get access token
    token_resp = req.post(f"{base}/v1/oauth2/token",
                          auth=(client_id, client_secret),
                          data={'grant_type': 'client_credentials'})
    access_token = token_resp.json().get('access_token', '')

    # Create order — amount in USD (approximate)
    usd_amount = round(booking.total_price / 278, 2)   # rough PKR→USD
    order_resp = req.post(
        f"{base}/v2/checkout/orders",
        headers={'Authorization': f'Bearer {access_token}',
                 'Content-Type': 'application/json'},
        json={'intent': 'CAPTURE',
              'purchase_units': [{'amount': {'currency_code': 'USD',
                                             'value': str(usd_amount)}}]})
    order_data = order_resp.json()
    return jsonify({'order_id': order_data.get('id', 'ERROR')})


@payment_bp.route('/payment/paypal/capture/<int:booking_id>', methods=['POST'])
@login_required
def paypal_capture(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    data    = request.get_json() or {}
    order_id = data.get('order_id', 'PAYPAL_DEMO')
    _mark_paid(booking, method='PayPal', payment_id=order_id)
    _send_ticket_email(booking)
    return jsonify({'success': True,
                    'redirect': url_for('payment.ticket_view', booking_id=booking.id)})


# ════════════════════════════════════════════════════════════════════════════
# CASH / BANK TRANSFER — Manual
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/cash/<int:booking_id>', methods=['POST'])
@login_required
def cash_payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    booking.payment_method = 'Cash/Bank Transfer'
    booking.payment_status = 'Pending'   # Admin baad mein approve karega
    db.session.commit()
    flash('Cash/Bank Transfer selected. Your booking is pending admin approval.', 'info')
    return redirect(url_for('payment.ticket_view', booking_id=booking.id))


@payment_bp.route('/payment/admin/approve/<int:booking_id>', methods=['POST'])
@login_required
def admin_approve_cash(booking_id):
    """Admin panel se cash payment approve karna"""
    if not current_user.is_admin:
        return jsonify({'error': 'Admin only'}), 403
    booking = Booking.query.get_or_404(booking_id)
    _mark_paid(booking, method='Cash/Bank Transfer',
               payment_id=f'CASH-{datetime.utcnow().strftime("%Y%m%d%H%M")}')
    _send_ticket_email(booking)
    flash(f'Booking {booking.booking_id} payment approved!', 'success')
    return redirect(url_for('admin.admin_bookings'))


# ════════════════════════════════════════════════════════════════════════════
# DEMO SUCCESS (sandbox mode)
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/payment/demo-success/<int:booking_id>')
@login_required
def demo_success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    method  = request.args.get('method', 'Demo')
    _mark_paid(booking, method=method,
               payment_id=f'DEMO-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}')
    _send_ticket_email(booking)
    flash(f'{method} payment simulated successfully! (Demo Mode)', 'success')
    return redirect(url_for('payment.ticket_view', booking_id=booking.id))


# ════════════════════════════════════════════════════════════════════════════
# TICKET VIEW PAGE + PDF DOWNLOAD
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/ticket/<int:booking_id>')
@login_required
def ticket_view(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard.dashboard'))
    qr_b64 = make_qr_base64(booking)
    return render_template('payment/ticket.html', booking=booking, qr_b64=qr_b64)


@payment_bp.route('/ticket/download/<int:booking_id>')
@login_required
def download_ticket(booking_id):
    """PDF ticket download"""
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin:
        flash('Access denied!', 'error')
        return redirect(url_for('dashboard.dashboard'))
    pdf_bytes = generate_ticket_pdf(booking)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'SkyBook-Ticket-{booking.booking_id}.pdf'
    )


# ════════════════════════════════════════════════════════════════════════════
# CANCELLATION + REFUND
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/booking/cancel-refund/<int:booking_id>', methods=['POST'])
@login_required
def cancel_with_refund(booking_id):
    from datetime import date
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Access denied!', 'error')
        return redirect(url_for('bookings.my_bookings'))
    if booking.status == 'Cancelled':
        flash('Already cancelled!', 'warning')
        return redirect(url_for('bookings.my_bookings'))
    if booking.travel_date <= date.today():
        flash('Cannot cancel today or past bookings.', 'error')
        return redirect(url_for('bookings.my_bookings'))

    refund_amt, fee_pct, refund_pct = booking.calculate_refund()

    booking.status              = 'Cancelled'
    booking.refund_amount       = refund_amt
    booking.refund_status       = 'Pending'
    booking.refund_requested_at = datetime.utcnow()
    if booking.payment_status == 'Paid':
        booking.payment_status = 'Partially_Refunded' if fee_pct > 0 else 'Refunded'

    # Give seats back
    booking.flight.available_seats += booking.passengers
    db.session.commit()

    _send_cancellation_email(booking, refund_amt, fee_pct, refund_pct)
    flash(
        f'Booking {booking.booking_id} cancelled. '
        f'PKR {refund_amt:,.0f} ({refund_pct}%) will be refunded within 5-7 business days.',
        'success'
    )
    return redirect(url_for('bookings.my_bookings'))


# ════════════════════════════════════════════════════════════════════════════
# QR VERIFY (public — airport staff scan kar ke dekh sakta hai)
# ════════════════════════════════════════════════════════════════════════════
@payment_bp.route('/verify/<booking_ref>')
def verify_ticket(booking_ref):
    booking = Booking.query.filter_by(booking_id=booking_ref).first()
    if not booking:
        return render_template('payment/verify.html', booking=None, valid=False)
    return render_template('payment/verify.html', booking=booking, valid=True)


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════
def _mark_paid(booking, method: str, payment_id: str):
    """Booking ko paid mark karo aur QR generate karo"""
    booking.payment_status  = 'Paid'
    booking.payment_method  = method
    booking.payment_id      = payment_id
    booking.status          = 'Confirmed'
    booking.pdf_generated   = True
    booking.ticket_qr_code  = make_qr_base64(booking)
    db.session.commit()


def _send_ticket_email(booking):
    """User ko PDF ticket email karo"""
    try:
        from flask_mail import Message
        from app import mail
        mail_user = current_app.config.get('MAIL_USERNAME', '')
        if 'your_email' in mail_user or not mail_user:
            print(f"\n📧 [DEMO] Ticket email to {booking.passenger_email} — "
                  f"Booking: {booking.booking_id}\n")
            return
        pdf_bytes = generate_ticket_pdf(booking)
        msg = Message(
            subject=f'SkyBook Ticket — {booking.booking_id}',
            recipients=[booking.passenger_email],
            html=f"""
            <h2>Your SkyBook E-Ticket ✈</h2>
            <p>Dear {booking.passenger_name},</p>
            <p>Your booking <strong>{booking.booking_id}</strong> is confirmed.</p>
            <p><b>Flight:</b> {booking.flight.flight_number} — 
               {booking.flight.from_city} → {booking.flight.to_city}<br>
               <b>Date:</b> {booking.travel_date}<br>
               <b>Departure:</b> {booking.flight.departure_time}<br>
               <b>Amount Paid:</b> PKR {booking.total_price:,.0f} via {booking.payment_method}</p>
            <p>Your e-ticket is attached as a PDF. Scan the QR code at the airport.</p>
            <p>Have a great flight! — SkyBook Team</p>
            """
        )
        msg.attach(f'SkyBook-{booking.booking_id}.pdf',
                   'application/pdf', pdf_bytes)
        mail.send(msg)
    except Exception as e:
        print(f"Email error (demo mode): {e}")


def _send_cancellation_email(booking, refund_amt, fee_pct, refund_pct):
    """Cancellation confirmation email"""
    try:
        from flask_mail import Message
        from app import mail
        mail_user = current_app.config.get('MAIL_USERNAME', '')
        if 'your_email' in mail_user or not mail_user:
            print(f"\n📧 [DEMO] Cancellation email to {booking.passenger_email} — "
                  f"Refund: PKR {refund_amt:,.0f}\n")
            return
        msg = Message(
            subject=f'SkyBook Booking Cancelled — {booking.booking_id}',
            recipients=[booking.passenger_email],
            html=f"""
            <h2>Booking Cancellation Confirmed</h2>
            <p>Dear {booking.passenger_name},</p>
            <p>Your booking <strong>{booking.booking_id}</strong> has been cancelled.</p>
            <table border="1" cellpadding="8" style="border-collapse:collapse">
              <tr><td><b>Original Amount</b></td><td>PKR {booking.total_price:,.0f}</td></tr>
              <tr><td><b>Cancellation Fee ({fee_pct}%)</b></td>
                  <td>PKR {booking.total_price * fee_pct / 100:,.0f}</td></tr>
              <tr><td><b>Refund Amount ({refund_pct}%)</b></td>
                  <td><b>PKR {refund_amt:,.0f}</b></td></tr>
            </table>
            <p>Refund will be credited to your original payment method within 5–7 business days.</p>
            <p>— SkyBook Team</p>
            """
        )
        mail.send(msg)
    except Exception as e:
        print(f"Cancellation email error: {e}")
