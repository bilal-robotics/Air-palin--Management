# ============================================
# routes/flight_routes.py - Flight Search & Listing
# ============================================

from flask import Blueprint, render_template, request, jsonify
from models import db, Flight
import requests
import os

flight_bp = Blueprint('flights', __name__)


# ============================================
# FLIGHT SEARCH PAGE
# ============================================
@flight_bp.route('/flights')
def search_flights():
    """Flight search page"""
    # URL se search parameters lo
    from_city = request.args.get('from_city', '').strip()
    to_city = request.args.get('to_city', '').strip()
    travel_date = request.args.get('date', '')
    passengers = request.args.get('passengers', 1, type=int)

    flights = []
    searched = False

    if from_city and to_city:
        searched = True
        # Database query: case-insensitive search
        # ilike = case insensitive LIKE
        flights = Flight.query.filter(
            Flight.from_city.ilike(f'%{from_city}%'),
            Flight.to_city.ilike(f'%{to_city}%'),
            Flight.is_active == True,
            Flight.available_seats >= passengers
        ).all()

    # Cities list for autocomplete
    cities = get_all_cities()

    return render_template(
        'flights/search.html',
        flights=flights,
        searched=searched,
        from_city=from_city,
        to_city=to_city,
        travel_date=travel_date,
        passengers=passengers,
        cities=cities
    )


# ============================================
# FLIGHT DETAILS PAGE
# ============================================
@flight_bp.route('/flight/<int:flight_id>')
def flight_detail(flight_id):
    """Single flight ki details"""
    flight = Flight.query.get_or_404(flight_id)
    return render_template('flights/detail.html', flight=flight)


# ============================================
# ALL FLIGHTS PAGE
# ============================================
@flight_bp.route('/all-flights')
def all_flights():
    """Saari flights list"""
    airline_filter = request.args.get('airline', '')
    flights = Flight.query

    if airline_filter:
        flights = flights.filter(Flight.airline_code == airline_filter)

    flights = flights.filter(Flight.is_active == True).all()
    airlines = db.session.query(Flight.airline, Flight.airline_code).distinct().all()

    return render_template('flights/all_flights.html',
                           flights=flights,
                           airlines=airlines,
                           selected_airline=airline_filter)


# ============================================
# LIVE FLIGHT TRACKING (API)
# ============================================
@flight_bp.route('/track-flight')
def track_flight():
    """Live flight tracking page"""
    return render_template('flights/tracking.html')


@flight_bp.route('/api/track/<flight_number>')
def api_track_flight(flight_number):
    """
    OpenSky API se live flight data fetch karta hai
    API = Application Programming Interface
    Matlab: doosre service se data mangna
    """
    api_key = os.environ.get('OPENSKY_API_KEY', 'YOUR_API_KEY_HERE')

    # Agar dummy key hai to mock data return karo
    if api_key == 'YOUR_API_KEY_HERE' or not api_key:
        return jsonify(get_mock_flight_data(flight_number))

    try:
        # Real API call (OpenSky Network - free tier)
        url = f"https://opensky-network.org/api/states/all?callsign={flight_number}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('states'):
                state = data['states'][0]
                return jsonify({
                    'success': True,
                    'flight_number': flight_number,
                    'latitude': state[6],
                    'longitude': state[5],
                    'altitude': state[7],
                    'velocity': state[9],
                    'on_ground': state[8],
                    'status': 'On Ground' if state[8] else 'In Air'
                })

        return jsonify(get_mock_flight_data(flight_number))

    except Exception as e:
        return jsonify(get_mock_flight_data(flight_number))


# ============================================
# HELPER FUNCTIONS
# ============================================
def get_all_cities():
    """Database se saari cities return karta hai"""
    from_cities = db.session.query(Flight.from_city).distinct().all()
    to_cities = db.session.query(Flight.to_city).distinct().all()
    all_cities = set()
    for c in from_cities:
        all_cities.add(c[0])
    for c in to_cities:
        all_cities.add(c[0])
    return sorted(list(all_cities))


def get_mock_flight_data(flight_number):
    """Demo mode ke liye fake flight tracking data"""
    import random
    return {
        'success': True,
        'demo_mode': True,
        'flight_number': flight_number,
        'latitude': 24.8607 + random.uniform(-5, 15),   # Around Pakistan
        'longitude': 67.0011 + random.uniform(-5, 15),
        'altitude': random.randint(8000, 12000),
        'velocity': random.randint(800, 950),
        'on_ground': False,
        'status': 'In Air',
        'origin': 'Karachi (KHI)',
        'destination': 'Dubai (DXB)',
        'estimated_arrival': '2h 15m',
        'message': 'Demo Mode - Real API key required for live tracking'
    }
