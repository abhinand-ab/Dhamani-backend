# app.py
import os
from flask import Flask, request, render_template, jsonify
import sqlite3
from datetime import datetime, timedelta
import requests
import math

app = Flask(__name__, template_folder='templates')
DATABASE = 'blood_donation.db'
GOOGLE_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')  # set this in your environment

# ------------------
# Database helpers
# ------------------
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create tables if not exists and add lat/lng columns if missing."""
    conn = get_db()
    cur = conn.cursor()

    # donors table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS donors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        blood_group TEXT,
        contact TEXT,
        location TEXT,          -- free-text address or label
        availability TEXT,
        last_donation_date TEXT,
        lat REAL,
        lng REAL
    )
    ''')

    # recipients table
    cur.execute('''
    CREATE TABLE IF NOT EXISTS recipients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER,
        blood_group TEXT,
        contact TEXT,
        location TEXT,
        urgency TEXT,
        lat REAL,
        lng REAL
    )
    ''')

    conn.commit()
    conn.close()

# initialize DB on startup
init_db()

# ------------------
# Utils: Geocode
# ------------------
def geocode_address(address: str):
    """Use Google Geocoding API to get lat/lng for an address.
       Returns (lat, lng) or raises Exception.
    """
    if not GOOGLE_API_KEY:
        raise RuntimeError('GOOGLE_MAPS_API_KEY not set in environment.')
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if data.get('status') != 'OK' or not data.get('results'):
        raise ValueError(f"Geocoding failed: {data.get('status')}, {data.get('error_message')}")
    loc = data['results'][0]['geometry']['location']
    return float(loc['lat']), float(loc['lng'])

# ------------------
# Utils: Distance (Haversine)
# ------------------
def haversine_distance_km(lat1, lng1, lat2, lng2):
    # Earth radius in km
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*(math.sin(dlambda/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ------------------
# Routes
# ------------------
@app.route('/')
def index():
    return "Welcome to the Blood Donation Backend with Google Maps features!"

@app.route('/register-donor', methods=['POST'])
def register_donor():
    data = request.get_json() or {}
    try:
        # required fields
        name = str(data.get('name', '')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group', '')).strip()
        contact = str(data.get('contact', '')).strip()
        location = data.get('location')  # can be address string or None
        # availability: 'Yes' or 'No'
        availability = str(data.get('availability', 'Yes')).strip()
        last_donation_date = data.get('last_donation_date')  # YYYY-MM-DD or None

        # lat,lng optional (preferred if user provides)
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is not None:
            lat = float(lat)
        if lng is not None:
            lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data types provided.'}), 400

    # validations
    if not name or not blood_group or not contact:
        return jsonify({'status': 'error', 'message': 'name, blood_group and contact are required.'}), 400
    if age <= 0:
        return jsonify({'status': 'error', 'message': 'Age must be positive.'}), 400
    if len(contact) < 10 or not contact.isdigit():
        return jsonify({'status': 'error', 'message': 'Invalid contact number.'}), 400
    valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    if blood_group not in valid_blood_groups:
        return jsonify({'status': 'error', 'message': 'Invalid blood group.'}), 400

    # last donation date restriction
    if last_donation_date:
        try:
            donation_date_obj = datetime.strptime(last_donation_date, '%Y-%m-%d')
            if datetime.now() - donation_date_obj < timedelta(days=90):
                return jsonify({'status': 'error', 'message': 'Donor must wait 3 months between donations.'}), 400
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # If lat/lng not provided, try geocoding from location string (if provided)
    if (lat is None or lng is None) and location:
        try:
            geocoded = geocode_address(location)
            lat, lng = geocoded
        except Exception as e:
            # don't fail registration - just continue without lat/lng but inform user
            return jsonify({'status': 'error', 'message': f'Geocoding failed: {e}'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO donors (name, age, blood_group, contact, location, availability, last_donation_date, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, blood_group, contact, location, availability, last_donation_date, lat, lng))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Donor registered!'})

@app.route('/register-recipient', methods=['POST'])
def register_recipient():
    data = request.get_json() or {}
    try:
        name = str(data.get('name', '')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group', '')).strip()
        contact = str(data.get('contact', '')).strip()
        location = data.get('location')
        urgency = str(data.get('urgency', '')).strip()
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is not None:
            lat = float(lat)
        if lng is not None:
            lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data types provided'}), 400

    # If lat/lng not provided, try geocoding from location string (if provided)
    if (lat is None or lng is None) and location:
        try:
            geocoded = geocode_address(location)
            lat, lng = geocoded
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Geocoding failed: {e}'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO recipients (name, age, blood_group, contact, location, urgency, lat, lng)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, blood_group, contact, location, urgency, lat, lng))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Recipient registered successfully!'})

# ------------------
# Viewing endpoints
# ------------------
@app.route('/view-donors', methods=['GET'])
def view_donors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM donors')
    rows = cursor.fetchall()
    conn.close()
    donors = [dict(row) for row in rows]
    return jsonify(donors)

@app.route('/view-recipients', methods=['GET'])
def view_recipients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipients')
    rows = cursor.fetchall()
    conn.close()
    recipients = [dict(row) for row in rows]
    return jsonify(recipients)

# ------------------
# Update / Delete endpoints (unchanged except lat/lng support)
# ------------------
@app.route('/update-donor/<int:donor_id>', methods=['PUT'])
def update_donor(donor_id):
    data = request.get_json() or {}
    try:
        name = str(data.get('name', '')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group', '')).strip()
        contact = str(data.get('contact', '')).strip()
        location = data.get('location')
        availability = str(data.get('availability', '')).strip()
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is not None:
            lat = float(lat)
        if lng is not None:
            lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data provided'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE donors
        SET name = ?, age = ?, blood_group = ?, contact = ?, location = ?, availability = ?, lat = ?, lng = ?
        WHERE id = ?
    ''', (name, age, blood_group, contact, location, availability, lat, lng, donor_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Donor updated successfully!'})

@app.route('/delete-donor/<int:donor_id>', methods=['DELETE'])
def delete_donor(donor_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM donors WHERE id = ?', (donor_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Donor deleted successfully!'})

@app.route('/update-recipient/<int:recipient_id>', methods=['PUT'])
def update_recipient(recipient_id):
    data = request.get_json() or {}
    try:
        name = str(data.get('name', '')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group', '')).strip()
        contact = str(data.get('contact', '')).strip()
        location = data.get('location')
        urgency = str(data.get('urgency', '')).strip()
        lat = data.get('lat')
        lng = data.get('lng')
        if lat is not None:
            lat = float(lat)
        if lng is not None:
            lng = float(lng)
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data provided'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE recipients
        SET name = ?, age = ?, blood_group = ?, contact = ?, location = ?, urgency = ?, lat = ?, lng = ?
        WHERE id = ?
    ''', (name, age, blood_group, contact, location, urgency, lat, lng, recipient_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Recipient updated successfully!'})

@app.route('/delete-recipient/<int:recipient_id>', methods=['DELETE'])
def delete_recipient(recipient_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipients WHERE id = ?', (recipient_id,))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'message': 'Recipient deleted successfully!'})

# ------------------
# Matching endpoint (keeps using exact location string or can use nearby)
# ------------------
@app.route('/match-donors/<int:recipient_id>', methods=['GET'])
def match_donors(recipient_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT blood_group, location, lat, lng FROM recipients WHERE id = ?', (recipient_id,))
    recipient = cursor.fetchone()
    if not recipient:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Recipient not found'}), 404

    blood_group = recipient['blood_group']
    rec_lat = recipient['lat']
    rec_lng = recipient['lng']
    rec_location = recipient['location']

    # If recipient has lat/lng, do nearby search within 10 km; otherwise exact location string match
    if rec_lat is not None and rec_lng is not None:
        radius_km = 10
        conn2 = get_db()
        cur2 = conn2.cursor()
        cur2.execute('SELECT * FROM donors WHERE blood_group = ? AND availability = "Yes" AND lat IS NOT NULL AND lng IS NOT NULL', (blood_group,))
        rows = cur2.fetchall()
        conn2.close()
        matches = []
        for row in rows:
            d = dict(row)
            dist = haversine_distance_km(rec_lat, rec_lng, d['lat'], d['lng'])
            if dist <= radius_km:
                d['distance_km'] = dist
                matches.append(d)
        matches.sort(key=lambda x: x.get('distance_km', 999))
    else:
        cursor.execute('''
            SELECT * FROM donors
            WHERE blood_group = ? AND location = ? AND availability = 'Yes'
        ''', (blood_group, rec_location))
        matches = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({'status': 'success', 'matches': matches})

# ------------------
# Nearby donors endpoint (Google Maps front-end will call this)
# ------------------
@app.route('/donors/nearby', methods=['GET'])
def donors_nearby():
    try:
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'lat and lng query parameters required'}), 400

    radius_km = float(request.args.get('radius_km', 5.0))
    blood_group = request.args.get('blood_group')  # optional
    # Basic bounding box to limit DB rows (approx)
    lat_deg = radius_km / 111.0  # ~111 km per lat degree
    lng_deg = radius_km / (111.320 * math.cos(math.radians(user_lat)) + 1e-9)

    min_lat = user_lat - lat_deg
    max_lat = user_lat + lat_deg
    min_lng = user_lng - lng_deg
    max_lng = user_lng + lng_deg

    conn = get_db()
    cur = conn.cursor()
    query = 'SELECT * FROM donors WHERE lat IS NOT NULL AND lng IS NOT NULL AND availability = "Yes"'
    params = []
    if blood_group:
        query += ' AND blood_group = ?'
        params.append(blood_group)
    query += ' AND lat BETWEEN ? AND ? AND lng BETWEEN ? AND ?'
    params.extend([min_lat, max_lat, min_lng, max_lng])

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        dist = haversine_distance_km(user_lat, user_lng, d['lat'], d['lng'])
        if dist <= radius_km:
            d['distance_km'] = round(dist, 3)
            results.append(d)

    # sort by distance
    results.sort(key=lambda x: x['distance_km'])
    return jsonify({'status': 'success', 'count': len(results), 'donors': results})

# ------------------
# Simple map view (frontend) that will request /donors/nearby
# ------------------
@app.route('/map')
def map_view():
    # will embed the browser API key in the page (make sure you use a restricted browser key)
    browser_key = os.environ.get('GOOGLE_MAPS_API_KEY')  # you can use a separate restricted browser key
    return render_template('map.html', google_maps_key=browser_key)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
