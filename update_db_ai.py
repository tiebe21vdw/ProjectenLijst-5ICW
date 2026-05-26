import sqlite3

conn = sqlite3.connect('registrants.db')
db = conn.cursor()

try:
    # Voeg kolom voor de AI score toe
    db.execute("ALTER TABLE projects ADD COLUMN ai_score INTEGER")
    # Voeg kolom voor de AI feedback toe
    db.execute("ALTER TABLE projects ADD COLUMN ai_feedback TEXT")
    conn.commit()
    print("Database succesvol geüpdatet met AI-kolommen!")
except sqlite3.OperationalError:
    print("De kolommen bestonden waarschijnlijk al.")
finally:
    conn.close()