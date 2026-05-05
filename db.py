import sqlite3

def create_database():
    conn = sqlite3.connect('SCA.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        studentID TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        year_level TEXT NOT NULL,
        rfid TEXT NOT NULL UNIQUE
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()
