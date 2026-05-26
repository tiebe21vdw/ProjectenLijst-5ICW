# --- IMPORTS ---
import sqlite3
import smtplib
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

app = Flask(__name__)
app.secret_key = 'super_geheime_sleutel_verander_dit'

# --- EMAIL CONFIGURATIE ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tiebe090408@gmail.com'  # Je eigen Gmail adres
app.config['MAIL_PASSWORD'] = 'rhpnlhbcltdmxfao'  # Je app-wachtwoord van Google
app.config['MAIL_DEFAULT_SENDER'] = 'tiebe090408@gmail.com'

s = URLSafeTimedSerializer(app.secret_key)

# Database connectie helper
def get_db_connection():
    conn = sqlite3.connect('registrants.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.context_processor
def inject_theme():
    theme = session.get('theme', 'light')
    if theme not in ['light', 'dark', 'ocean', 'dark-neon', 'soft-nature', 'sunset', 'frosted-ice', 'retro-gaming', 'coffee', 'cyberpunk']:
        theme = 'light'
    return {'theme_class': theme}

# --- AUTOMATISCHE ADMIN MAKER ---
# Dit zorgt ervoor dat de leerkracht en jij automatisch admin worden als jullie registreren
def check_and_assign_admins():
    admins_to_set = ['tiebe090408@gmail.com', 'nicky.vergauwen@sjabi.be']  # Voeg hier e-mailadressen toe die automatisch admin moeten worden
    conn = get_db_connection()
    db = conn.cursor()
    for email in admins_to_set:
        db.execute("UPDATE users SET role = 'admin', verified = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()

# Zorg dat de projects-tabel een admin-commentaarkolom heeft
# Dit maakt het veilig om bestaande databases te upgraden.
def ensure_project_comment_column():
    conn = get_db_connection()
    db = conn.cursor()
    table_exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
    if not table_exists:
        conn.close()
        return
    columns = [row['name'] for row in db.execute("PRAGMA table_info(projects)").fetchall()]
    if 'admin_comment' not in columns:
        db.execute("ALTER TABLE projects ADD COLUMN admin_comment TEXT")
        conn.commit()
    conn.close()

# Zorg dat de projects-tabel een visibility-kolom heeft
# Dit maakt het veilig om bestaande databases te upgraden.
def ensure_project_visibility_column():
    conn = get_db_connection()
    db = conn.cursor()
    table_exists = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone()
    if not table_exists:
        conn.close()
        return
    columns = [row['name'] for row in db.execute("PRAGMA table_info(projects)").fetchall()]
    if 'visibility' not in columns:
        db.execute("ALTER TABLE projects ADD COLUMN visibility TEXT DEFAULT 'public'")
        conn.commit()
    conn.close()

# Native mailfunctie met ingebouwde foutafhandeling
def send_email(subject, recipients, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = ', '.join(recipients) if isinstance(recipients, (list, tuple)) else recipients
    msg.set_content(body)

    with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
        if app.config.get('MAIL_USE_TLS'):
            server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.send_message(msg)

@app.route('/set_theme', methods=['POST'])
def set_theme():
    theme = request.form.get('theme', 'light')
    allowed_themes = ['light', 'dark', 'ocean', 'dark-neon', 'soft-nature', 'sunset', 'frosted-ice', 'retro-gaming', 'coffee', 'cyberpunk']
    if theme not in allowed_themes:
        theme = 'light'
    session['theme'] = theme
    return redirect(request.referrer or url_for('index'))

# Zorg ervoor dat de database kolommen aanwezig zijn bij import
ensure_project_comment_column()
ensure_project_visibility_column()

# --- HOME PAGINA ---
@app.route('/')
def index():
    conn = get_db_connection()
    db = conn.cursor()
    
    # Met deze JOIN halen we de projecten op én de naam van de gebruiker die het gemaakt heeft!
    if session.get('user_role') == 'admin':
        projecten = db.execute('''
            SELECT projects.*, users.name AS creator_name 
            FROM projects 
            JOIN users ON projects.user_id = users.id
        ''').fetchall()
    elif 'user_id' in session:
        projecten = db.execute('''
            SELECT projects.*, users.name AS creator_name 
            FROM projects 
            JOIN users ON projects.user_id = users.id
            WHERE COALESCE(visibility, 'public') = 'public' OR projects.user_id = ?
        ''', (session['user_id'],)).fetchall()
    else:
        projecten = db.execute('''
            SELECT projects.*, users.name AS creator_name 
            FROM projects 
            JOIN users ON projects.user_id = users.id
            WHERE COALESCE(visibility, 'public') = 'public'
        ''').fetchall()
    conn.close()

    if 'user_name' in session:
        current_user = session['user_name']
        is_guest = False
    else:
        current_user = "Gast"
        is_guest = True
    
    return render_template('index.html', username=current_user, is_guest=is_guest, projecten=projecten)


# --- GEBRUIKER OF ADMIN: PROJECT TOEVOEGEN ---
@app.route('/upload_project', methods=['POST', 'GET'])
def upload_project():
    if 'user_id' not in session:
        flash("Je moet eerst inloggen om een project toe te voegen!", "error")
        return redirect(url_for('login'))

    if request.method == 'GET':
        # Toon de upload-pagina
        return render_template('upload_project.html')

    # POST -> verwerk formulier
    title = request.form.get('title')
    description = request.form.get('description')
    link = request.form.get('link')
    visibility = request.form.get('visibility', 'public')
    user_id = session['user_id']

    if title and description:
        conn = get_db_connection()
        db = conn.cursor()
        db.execute("INSERT INTO projects (title, description, link, user_id, visibility) VALUES (?, ?, ?, ?, ?)", 
                   (title, description, link, user_id, visibility))
        conn.commit()
        conn.close()
        flash("Je project is succesvol toegevoegd!", "success")
        return redirect(url_for('index'))

    flash("Vul tenminste een titel en beschrijving in!", "error")
    return redirect(request.referrer or url_for('upload_project'))


# --- PROJECT VERWIJDEREN (USER & ADMIN) ---
@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if 'user_id' not in session:
        flash("Je moet eerst inloggen!", "error")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    db = conn.cursor()
    project = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    
    if not project:
        conn.close()
        flash("Project niet gevonden!", "error")
        return redirect(url_for('index'))
        
    if project['user_id'] == session['user_id'] or session.get('user_role') == 'admin':
        db.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        flash("Project succesvol verwijderd!", "success")
    else:
        flash("Toegang geweigerd! Dit is niet jouw project.", "error")
        
    conn.close()
    return redirect(request.referrer or url_for('index'))


@app.route('/project_comment/<int:project_id>', methods=['POST'])
def project_comment(project_id):
    if session.get('user_role') != 'admin':
        flash("Alleen admins mogen commentaar toevoegen.", "error")
        return redirect(request.referrer or url_for('index'))

    comment = request.form.get('comment', '').strip()
    conn = get_db_connection()
    db = conn.cursor()
    project = db.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()

    if not project:
        conn.close()
        flash("Project niet gevonden.", "error")
        return redirect(request.referrer or url_for('index'))

    db.execute("UPDATE projects SET admin_comment = ? WHERE id = ?", (comment, project_id))
    conn.commit()
    conn.close()

    flash("Commentaar succesvol opgeslagen.", "success")
    return redirect(request.referrer or url_for('index'))


# --- REGISTREREN ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not name or not email or not password:
            return render_template('register.html', error="Vul alle velden in!")
            
        hash_veilig = generate_password_hash(password)
        
        conn = get_db_connection()
        db = conn.cursor()
        try:
            db.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, hash_veilig))
            conn.commit()
            
            # Voer de automatische admin check uit mocht dit e-mailadres in de lijst staan
            conn.close()
            check_and_assign_admins()
            
            # --- VERIFICATIE MAIL GENEREREN ---
            token = s.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=token, _external=True)
            
            email_body = (
                f'Beste {name},\n\n'
                f'Klik op de volgende link om je account te activeren:\n{link}\n\n'
                'Deze link is 30 minuten geldig.'
            )
            
            send_email('Verifieer je e-mailadres', [email], email_body)
            
            return render_template('confirm_notice.html', email=email)
            
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="Dit e-mailadres is al geregistreerd!")
        except Exception as e:
            if 'conn' in locals(): conn.close()
            return render_template('register.html', error=f"Er ging iets mis met het sturen van de mail: {e}")
            
    return render_template('register.html')


# --- VERIFICATIE ROUTE ---
@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=1800)
    except SignatureExpired:
        return render_template('login.html', error="De verificatielink is verlopen! Registreer je opnieuw.")
    except BadTimeSignature:
        return render_template('login.html', error="Ongeldige verificatielink!")

    conn = get_db_connection()
    db = conn.cursor()
    db.execute("UPDATE users SET verified = 1 WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    return render_template('login.html', success="Je e-mailadres is succesvol geverifieerd! Je kunt nu inloggen.")


# --- INLOGGEN ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        db = conn.cursor()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            if user['verified'] == 0:
                return render_template('login.html', error="Je moet eerst je e-mailadres verifiëren!")
                
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            return redirect(url_for('index'))
        else:
            flash("Ongeldig e-mailadres of wachtwoord!", "error")
            return redirect(url_for('login'))
    return render_template('login.html')


# --- UITLOGGEN ---
@app.route('/logout')
def logout():
    session.clear()
    flash("Je bent succesvol uitgelogd!", "success")
    return redirect(url_for('index'))


# --- WACHTWOORD VERGETEN ---
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            return render_template('forgot_password.html', error="Vul je e-mailadres in!")
            
        conn = get_db_connection()
        db = conn.cursor()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if user:
            token = s.dumps(email, salt='password-reset')
            link = url_for('reset_password', token=token, _external=True)
            
            email_body = (
                f'Beste {user["name"]},\n\n'
                f'Je hebt een verzoek ingediend om je wachtwoord te herstellen. '
                f'Klik op de onderstaande link om een nieuw wachtwoord te kiezen:\n{link}\n\n'
                'Deze link is 10 minuten geldig. Als jij dit niet was, kun je deze mail negeren.'
            )
            try:
                send_email('Wachtwoord herstellen', [email], email_body)
            except Exception as e:
                return render_template('forgot_password.html', error=f"Fout bij verzenden: {e}")

        return render_template('login.html', success="Als dit e-mailadres bekend is, is er een herstellink verzonden!")

    return render_template('forgot_password.html')


# --- NIEUW WACHTWOORD INSTELLEN ---
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset', max_age=600)
    except SignatureExpired:
        return render_template('login.html', error="De herstellink is verlopen! Vraag een nieuwe aan.")
    except BadTimeSignature:
        return render_template('login.html', error="Ongeldige herstellink!")

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or not confirm_password:
            return render_template('reset_password.html', token=token, error="Vul alle velden in!")
            
        if password != confirm_password:
            return render_template('reset_password.html', token=token, error="Wachtwoorden komen niet overeen!")
            
        hash_veilig = generate_password_hash(password)
        
        conn = get_db_connection()
        db = conn.cursor()
        db.execute("UPDATE users SET password_hash = ? WHERE email = ?", (hash_veilig, email))
        conn.commit()
        conn.close()
        
        return render_template('login.html', success="Je wachtwoord is succesvol aangepast! Je kunt nu inloggen.")

    return render_template('reset_password.html', token=token)


# --- KLASBEHEER: LEERKRACHT DASHBOARD ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_role' not in session or session['user_role'] != 'admin':
        return "Toegang geweigerd! Je bent geen leerkracht.", 403
        
    conn = get_db_connection()
    db = conn.cursor()
    
    # Haal de lijst op van alle gebruikers
    gebruikers = db.execute("SELECT id, name, email, role, verified FROM users").fetchall()
    
    # NIEUW: Tellers voor de statistiek-blokken in het dashboard
    aantal_leerlingen = db.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()[0]
    aantal_admins = db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           gebruikers=gebruikers, 
                           aantal_leerlingen=aantal_leerlingen, 
                           aantal_admins=aantal_admins)


# --- ADMIN: GEBRUIKER VERWIJDEREN ---
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def admin_delete_user(user_id):
    if 'user_role' not in session or session['user_role'] != 'admin':
        return "Toegang geweigerd!", 403
        
    conn = get_db_connection()
    db = conn.cursor()
    
    if user_id == session['user_id']:
        conn.close()
        return "Je kunt je eigen admin-account niet verwijderen via het dashboard!", 400
        
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_dashboard'))


# --- PROFIELPAGINA ---
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    db = conn.cursor()
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        
        if not new_name:
            user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
            conn.close()
            return render_template('profile.html', user=user, error="Naam mag niet leeg zijn!")
            
        db.execute("UPDATE users SET name = ? WHERE id = ?", (new_name, session['user_id']))
        conn.commit()
        session['user_name'] = new_name
        
    user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    conn.close()
    
    success_msg = "Profiel succesvol bijgewerkt!" if request.method == 'POST' else None
    return render_template('profile.html', user=user, success=success_msg)


# --- GEBRUIKER VERWIJDERT EIGEN ACCOUNT ---
@app.route('/profile/delete_own_account', methods=['POST'])
def delete_own_account():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    db = conn.cursor()
    db.execute("DELETE FROM users WHERE id = ?", (session['user_id'],))
    conn.commit()
    conn.close()
    
    session.clear()
    return render_template('login.html', success="Je account is permanent verwijderd. Jammer dat je weggaat!")


if __name__ == '__main__':
    # Voer eenmalig de check uit bij het opstarten van de server
    check_and_assign_admins()
    app.run(debug=True)