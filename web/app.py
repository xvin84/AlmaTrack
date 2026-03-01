import sqlite3
import httpx
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.secret_key = "change-me-in-production"

API_BASE_URL = "http://127.0.0.1:8000/api"

def get_db_connection():
    conn = sqlite3.connect('almatrack.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.before_request
def check_session_validity():
    # Force re-login if the user is logged in but has an outdated session from older sprints
    if session.get('logged_in') and 'moderator_priority' not in session:
        session.clear()
        return redirect(url_for('index'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    conn = get_db_connection()
    mod = conn.execute("SELECT * FROM moderators WHERE username = ?", (username,)).fetchone()
    conn.close()
    
    if mod and check_password_hash(mod['password_hash'], password):
        session['logged_in'] = True
        session['moderator_id'] = mod['id']
        session['moderator_username'] = mod['username']
        session['moderator_priority'] = mod['priority']
        return redirect(url_for('dashboard'))
        
    flash('Неверный логин или пароль')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    
    try:
        req = httpx.get(f"{API_BASE_URL}/stats/summary", timeout=5.0)
        stats = req.json()
    except Exception:
        stats = {"summary": {}, "charts": {}}

    return render_template('dashboard.html', stats=stats)

@app.route('/requests')
def requests_page():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        req_p = httpx.get(f"{API_BASE_URL}/admin/pending", timeout=5.0)
        pending_users = req_p.json()
    except Exception:
        pending_users = []
    
    return render_template('requests.html', pending_users=pending_users)

@app.route('/approve/<int:user_id>', methods=['POST'])
def approve(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        httpx.post(f"{API_BASE_URL}/admin/approve/{user_id}", timeout=5.0)
    except Exception as e:
        flash(f"Ошибка при одобрении: {e}")
    return redirect(url_for('requests_page'))

@app.route('/reject/<int:user_id>', methods=['POST'])
def reject(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        httpx.post(f"{API_BASE_URL}/admin/reject/{user_id}", timeout=5.0)
    except Exception as e:
        flash(f"Ошибка при отклонении: {e}")
    return redirect(url_for('requests_page'))

@app.route('/approve_all', methods=['POST'])
def approve_all():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        httpx.post(f"{API_BASE_URL}/admin/approve_all", timeout=10.0)
    except Exception as e:
        flash(f"Ошибка: {e}")
    return redirect(url_for('requests_page'))

@app.route('/reject_all', methods=['POST'])
def reject_all():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        httpx.post(f"{API_BASE_URL}/admin/reject_all", timeout=10.0)
    except Exception as e:
        flash(f"Ошибка: {e}")
    return redirect(url_for('requests_page'))

@app.route('/api/admin/pending')
def api_admin_pending():
    if not session.get('logged_in'):
        return jsonify([])
    try:
        req = httpx.get(f"{API_BASE_URL}/admin/pending", timeout=5.0)
        return jsonify(req.json())
    except Exception:
        return jsonify([])

@app.route('/events')
def events():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('events.html')

@app.route('/analytics')
def analytics():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('analytics.html')

@app.route('/alumni')
def alumni():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    conn = get_db_connection()
    students = conn.execute('''
        SELECT u.telegram_id, u.full_name, u.faculty, u.graduation_year, e.company_name, e.position_level 
        FROM users u 
        LEFT JOIN employment e ON u.telegram_id = e.user_id AND e.is_current = 1
        WHERE u.privacy_level < 2 AND u.status = 'approved'
        ORDER BY u.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('alumni.html', students=students)

@app.route('/moderators')
def moderators():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    if session.get('moderator_priority') != 1:
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    mods = conn.execute("SELECT * FROM moderators ORDER BY priority, created_at").fetchall()
    conn.close()
    return render_template('moderators.html', moderators=mods)

@app.route('/add_moderator', methods=['POST'])
def add_moderator():
    if not session.get('logged_in') or session.get('moderator_priority') != 1:
        return redirect(url_for('dashboard'))
    username = request.form.get('username')
    full_name = request.form.get('full_name')
    password = request.form.get('password')
    priority = int(request.form.get('priority', 2))
    conn = get_db_connection()
    try:
        hash_pw = generate_password_hash(password)
        conn.execute("INSERT INTO moderators (username, full_name, password_hash, priority) VALUES (?, ?, ?, ?)",
                     (username, full_name, hash_pw, priority))
        conn.commit()
    except sqlite3.IntegrityError:
        flash("Логин уже существует")
    conn.close()
    return redirect(url_for('moderators'))

@app.route('/delete_moderator/<int:mod_id>', methods=['POST'])
def delete_moderator_route(mod_id):
    if not session.get('logged_in') or session.get('moderator_priority') != 1:
        return redirect(url_for('dashboard'))
    if mod_id == session.get('moderator_id'):
        flash("Нельзя удалить самого себя!")
        return redirect(url_for('moderators'))
    conn = get_db_connection()
    conn.execute("DELETE FROM moderators WHERE id = ?", (mod_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('moderators'))

def ensure_admin():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM moderators").fetchone()[0]
    if count == 0:
        hash_pw = generate_password_hash("almatrack2025")
        conn.execute(
            "INSERT INTO moderators (username, full_name, password_hash, priority) VALUES (?, ?, ?, ?)",
            ("admin", "Главный Администратор", hash_pw, 1)
        )
        conn.commit()
    conn.close()

if __name__ == '__main__':
    ensure_admin()
    app.run(host='0.0.0.0', port=5000, debug=False)
