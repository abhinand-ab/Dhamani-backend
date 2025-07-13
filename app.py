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
@app.route('/register-donor', methods=['POST'])
def register_donor():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO donors (name, age, blood_group, contact, location, availability)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['age'], data['blood_group'], data['contact'], data['location'], data['availability']))
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
    name = data.get('name')
    age = data.get('age')
    blood_group = data.get('blood_group')
    contact = data.get('contact')
    location = data.get('location')
    urgency = data.get('urgency')

    conn = sqlite3.connect('blood_donation.db')
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

if __name__ == '__main__':
    app.run(port=5000)