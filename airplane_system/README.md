# ✈ SkyBook — Airplane Management & Ticket Booking System

A complete full-stack web application for flight search, booking management, and live flight tracking. Built with **Python Flask** + **SQLite** + **HTML/CSS/JS**.

---

## 🚀 Quick Start (Run in 3 Steps)

```bash
# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Run the app
python app.py

# Step 3: Open browser
# Go to: http://127.0.0.1:5000
```

**Demo Login:**
- 👤 Admin: `admin@skybook.com` / `admin123`
- 🔑 OTP (demo mode): Check your terminal/console

---

## 📁 Project Structure

```
airplane_system/
│
├── app.py                      ← Flask app entry point, config, seed data
├── models.py                   ← Database tables (User, Flight, Booking)
├── requirements.txt            ← Python packages needed
├── .env                        ← Environment variables (dummy values)
├── database.db                 ← SQLite database (auto-created)
│
├── routes/                     ← URL handlers (Blueprints)
│   ├── auth_routes.py          ← /login, /signup, /logout, /verify-otp
│   ├── flight_routes.py        ← /flights, /all-flights, /track-flight
│   ├── booking_routes.py       ← /book, /my-bookings, /cancel
│   ├── dashboard_routes.py     ← /dashboard
│   └── admin_routes.py         ← /admin/*
│
├── templates/                  ← Jinja2 HTML templates
│   ├── base.html               ← Navbar, footer, flash messages
│   ├── index.html              ← Home page with search form
│   ├── auth/
│   │   ├── login.html
│   │   ├── signup.html
│   │   └── verify_otp.html
│   ├── flights/
│   │   ├── search.html         ← Search results
│   │   ├── all_flights.html    ← Browse all flights
│   │   └── tracking.html       ← Live tracking map
│   ├── bookings/
│   │   ├── book.html           ← Booking form
│   │   ├── confirmation.html   ← Success page (confetti!)
│   │   ├── my_bookings.html    ← Booking history
│   │   └── detail.html         ← E-ticket view
│   ├── dashboard/
│   │   └── dashboard.html      ← User dashboard with stats
│   └── admin/
│       ├── dashboard.html
│       ├── flights.html
│       ├── users.html
│       └── bookings.html
│
└── static/
    ├── css/style.css           ← Complete stylesheet (responsive)
    └── js/main.js              ← Navbar, animations, UI logic
```

---

## 🔹 Features Explained

### 1. User Authentication
- Signup with email + password hashing (`werkzeug.security`)
- OTP email verification (prints to console in demo mode)
- Session-based login with Flask-Login
- Remember me functionality

### 2. Flight System
- 13 pre-loaded flights: **PIA, Emirates, Qatar Airways, Air Arabia, Serene Air**
- Routes: Karachi, Lahore, Islamabad, Dubai, Doha, London, New York, Sharjah
- Filter by airline, search by city pair

### 3. Ticket Booking
- Economy / Business / First class pricing
- Seat availability check
- Unique booking ID format: `SKY-2024-XXXXXX`
- Cancel booking (with seat restoration)

### 4. Live Flight Tracking
- OpenSky Network API integration
- Demo mode with simulated location data
- Interactive Leaflet.js map
- Shows altitude, speed, status

### 5. Dashboard
- Booking stats, upcoming trips
- Total spend calculator
- Quick action shortcuts

### 6. Admin Panel
- `/admin/` — Overview + revenue stats
- `/admin/flights` — Toggle flight active/inactive
- `/admin/users` — View all users
- `/admin/bookings` — All bookings across users

---

## 🗄️ Database Tables

```sql
-- users table
id, name, email, password (hashed), is_verified, otp, otp_created_at, is_admin, created_at

-- flights table
id, flight_number, airline, airline_code, from_city, to_city,
from_airport, to_airport, departure_time, arrival_time, duration,
price, total_seats, available_seats, aircraft_type, is_active

-- bookings table
id, booking_id, user_id (FK), flight_id (FK), travel_date,
passengers, seat_class, total_price, status, passenger_name,
passenger_email, passenger_phone, created_at
```

---

## 🔐 Environment Variables (.env)

```env
SECRET_KEY=your_super_secret_key
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_gmail_app_password
OPENSKY_API_KEY=YOUR_OPENSKY_API_KEY_HERE
```

**To enable real email:** Replace dummy values with Gmail App Password
**To enable live tracking:** Get free key from https://opensky-network.org/

---

## 🧠 Key Concepts Used

| Concept | Where Used | Explanation |
|--------|-----------|-------------|
| Flask Blueprint | routes/*.py | Group related routes in separate files |
| SQLAlchemy ORM | models.py | Python classes = database tables |
| Flask-Login | auth_routes.py | Manages user sessions |
| Password Hashing | signup | `generate_password_hash()` — never store plain text |
| Jinja2 Templates | templates/ | `{{ variable }}` and `{% if %}` in HTML |
| AJAX/Fetch API | tracking.html | JS calls Python API without page reload |
| IntersectionObserver | main.js | Scroll animations |
| Foreign Keys | Booking model | Links bookings → users → flights |

---

## 🌐 All URL Routes

| URL | Method | Description |
|-----|--------|-------------|
| `/` | GET | Home page |
| `/signup` | GET/POST | Register new account |
| `/login` | GET/POST | User login |
| `/logout` | GET | Logout |
| `/verify-otp` | GET/POST | Email OTP verification |
| `/flights` | GET | Search flights by city |
| `/all-flights` | GET | Browse all flights |
| `/track-flight` | GET | Live tracking page |
| `/api/track/<flight>` | GET | JSON tracking data |
| `/book/<flight_id>` | GET/POST | Book a flight |
| `/booking/confirmation/<id>` | GET | Booking success |
| `/my-bookings` | GET | User booking history |
| `/booking/<id>` | GET | Single booking detail |
| `/booking/cancel/<id>` | POST | Cancel booking |
| `/dashboard` | GET | User dashboard |
| `/admin/` | GET | Admin dashboard |
| `/admin/flights` | GET | Manage flights |
| `/admin/users` | GET | View all users |
| `/admin/bookings` | GET | All bookings |

---

## 🎯 Portfolio Notes

This project demonstrates:
- **MVC Architecture** — Models, Routes (Controller), Templates (View)
- **RESTful routing** — Proper GET/POST usage
- **Database relationships** — One-to-many with foreign keys
- **Security** — Password hashing, session management, CSRF-safe forms
- **API integration** — External REST API call with fallback
- **Responsive design** — Mobile + desktop CSS with CSS variables

---

*Built for GitHub Portfolio & LinkedIn Showcase | Educational Project*
