import sqlite3

def init_db():
    conn = sqlite3.connect('blood_donation.db')
    cursor = conn.cursor()

    # Drop tables if they exist
    cursor.execute('DROP TABLE IF EXISTS donors')
    cursor.execute('DROP TABLE IF EXISTS recipients')

    # Create donors table
    cursor.execute('''
        CREATE TABLE donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            blood_group TEXT NOT NULL,
            contact TEXT NOT NULL,
            location TEXT NOT NULL,
            availability TEXT NOT NULL,
            last_donation_date DATE NOT NULL
        )
    ''')
    # Create recipients table
    cursor.execute('''
        CREATE TABLE recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            blood_group TEXT NOT NULL,
            contact TEXT NOT NULL,
            location TEXT NOT NULL,
            urgency TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('Database initialized.')
