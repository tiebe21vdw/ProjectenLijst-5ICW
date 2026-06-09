import sqlite3
import os

def init_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'registrants.db')
    
    conn = sqlite3.connect(DATABASE_PATH)
    db = conn.cursor()
    db.execute('DROP TABLE IF EXISTS users') # Let op: wist tijdelijk je oude test-accounts weer even
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            verified INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user'  -- HIERMEE HOUDEN WE DE ROL BIJ
        )
    ''')

    # Pas dit aan in init_D8.py binnen je init_db() functie
    db.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            link TEXT,
            github_link TEXT,
            visibility TEXT DEFAULT 'public',
            user_id INTEGER NOT NULL, -- HIERMEE KOPPELEN WE HET PROJECT AAN EEN GEBRUIKER
            ai_score INTEGER DEFAULT 0,
            ai_feedback TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database is succesvol geïnitialiseerd!")