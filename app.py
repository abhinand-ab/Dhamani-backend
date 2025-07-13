from flask import Flask, request, render_template, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = 'blood_donation.db'

# Helper to connect to DB
def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/')
def index():
    return "Welcome to the Blood Donation Backend!"

# Donor Registration API
from datetime import datetime, timedelta

@app.route('/register-donor', methods=['POST'])
def register_donor():
    data = request.get_json()

    try:
        # Extract and convert data safely
        name = str(data.get('name')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group')).strip()
        contact = str(data.get('contact')).strip()
        location = str(data.get('location')).strip()
        availability = str(data.get('availability')).strip()
        last_donation_date = data.get('last_donation_date')  # Expecting format 'YYYY-MM-DD' or None
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data types provided.'}), 400

    # Field validations
    if not name or not blood_group or not contact or not location or not availability:
        return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400

    if age <= 0:
        return jsonify({'status': 'error', 'message': 'Age must be a positive integer.'}), 400

    if len(contact) < 10 or not contact.isdigit():
        return jsonify({'status': 'error', 'message': 'Invalid contact number.'}), 400

    valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    if blood_group not in valid_blood_groups:
        return jsonify({'status': 'error', 'message': 'Invalid blood group.'}), 400

    # Check 3-month donation restriction
    if last_donation_date:
        try:
            donation_date_obj = datetime.strptime(last_donation_date, '%Y-%m-%d')
            if datetime.now() - donation_date_obj < timedelta(days=90):
                return jsonify({'status': 'error', 'message': 'Donor must wait 3 months between donations.'}), 400
        except ValueError:
            return jsonify({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    else:
        last_donation_date = None  # Optional field

    # Insert into DB
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO donors (name, age, blood_group, contact, location, availability, last_donation_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (name, age, blood_group, contact, location, availability, last_donation_date))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Donor registered!'})

@app.route('/search-donors', methods=['GET'])
def search_donors():
    blood_group = request.args.get('blood_group')
    location = request.args.get('location')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM donors
        WHERE blood_group = ? AND location = ?
    ''', (blood_group, location))

    donors = cursor.fetchall()
    conn.close()

    result = []
    for donor in donors:
        result.append({
            'id': donor[0],
            'name': donor[1],
            'age': donor[2],
            'blood_group': donor[3],
            'contact': donor[4],
            'location': donor[5],
            'availability': donor[6]
        })

    return jsonify(result)
@app.route('/register-recipient', methods=['POST'])
def register_recipient():
    data = request.get_json()

    try:
        name = str(data.get('name')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group')).strip()
        contact = str(data.get('contact')).strip()
        location = str(data.get('location')).strip()
        urgency = str(data.get('urgency')).strip()

    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data types provided'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO recipients (name, age, blood_group, contact, location, urgency)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, age, blood_group, contact, location, urgency))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Recipient registered successfully!'})

@app.route('/view-donors', methods=['GET'])
def view_donors():
    conn = sqlite3.connect('blood_donation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM donors')
    rows = cursor.fetchall()
    conn.close()

    donors = []
    for row in rows:
        donors.append({
            'id': row[0],
            'name': row[1],
            'age': row[2],
            'blood_group': row[3],
            'contact': row[4],
            'location': row[5],
            'availability': row[6]
        })

    return jsonify(donors)

@app.route('/view-recipients', methods=['GET'])
def view_recipients():
    conn = sqlite3.connect('blood_donation.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipients')
    rows = cursor.fetchall()
    conn.close()

    recipients = []
    for row in rows:
        recipients.append({
            'id': row[0],
            'name': row[1],
            'age': row[2],
            'blood_group': row[3],
            'contact': row[4],
            'location': row[5],
            'urgency': row[6]
        })

    return jsonify(recipients)

@app.route('/update-donor/<int:donor_id>', methods=['PUT'])
def update_donor(donor_id):
    data = request.get_json()
    try:
        name = str(data.get('name')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group')).strip()
        contact = str(data.get('contact')).strip()
        location = str(data.get('location')).strip()
        availability = str(data.get('availability')).strip()
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data provided'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE donors
        SET name = ?, age = ?, blood_group = ?, contact = ?, location = ?, availability = ?
        WHERE id = ?
    ''', (name, age, blood_group, contact, location, availability, donor_id))
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
    data = request.get_json()
    try:
        name = str(data.get('name')).strip()
        age = int(data.get('age'))
        blood_group = str(data.get('blood_group')).strip()
        contact = str(data.get('contact')).strip()
        location = str(data.get('location')).strip()
        urgency = str(data.get('urgency')).strip()
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Invalid data provided'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE recipients
        SET name = ?, age = ?, blood_group = ?, contact = ?, location = ?, urgency = ?
        WHERE id = ?
    ''', (name, age, blood_group, contact, location, urgency, recipient_id))
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

@app.route('/match-donors/<int:recipient_id>', methods=['GET'])
def match_donors(recipient_id):
    conn = get_db()
    cursor = conn.cursor()

    # Get recipient details
    cursor.execute('SELECT blood_group, location FROM recipients WHERE id = ?', (recipient_id,))
    recipient = cursor.fetchone()
    
    if not recipient:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Recipient not found'}), 404

    blood_group, location = recipient

    # Get matching donors
    cursor.execute('''
        SELECT * FROM donors
        WHERE blood_group = ? AND location = ? AND availability = 'Yes'
    ''', (blood_group, location))

    matches = cursor.fetchall()
    conn.close()

    donors = []
    for row in matches:
        donors.append({
            'id': row[0],
            'name': row[1],
            'age': row[2],
            'blood_group': row[3],
            'contact': row[4],
            'location': row[5],
            'availability': row[6]
        })

    return jsonify({'status': 'success', 'matches': donors})


if __name__ == '__main__':
    app.run(port=5000)