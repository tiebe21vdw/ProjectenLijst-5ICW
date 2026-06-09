import sqlite3
import os

# Maak verbinding met je database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'registrants.db')

conn = sqlite3.connect(DATABASE_PATH)
db = conn.cursor()

# VUL HIER HET E-MAILADRES IN WAARMEE JE GEBRUIKER IS ANGEMAAKT:
jouw_email = 'tiebe090408@gmail.com'  # <-- PAS DIT AAN NAAR HET E-MAILADRES VAN JE ADMIN-ACCOUNT

# Geef dit account de admin-rol en zet verified op 1 (veiligheids-bypass)
db.execute("UPDATE users SET role = 'admin', verified = 1 WHERE email = ?", (jouw_email,))

conn.commit()
conn.close()

print(f"🚀 Succes! Het account {jouw_email} is nu live geüpgraded naar ADMIN!")