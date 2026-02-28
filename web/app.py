import sqlite3
import httpx
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "change-me-in-production"

API_BASE_URL = "http://127.0.0.1:8000/api"

def get_db_connection():
    conn = sqlite3.connect('almatrack.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template('login.html')
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'admin' and request.form['password'] == 'almatrack2025':
        session['logged_in'] = True
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
        
    try:
        req_p = httpx.get(f"{API_BASE_URL}/admin/pending", timeout=5.0)
        pending_users = req_p.json()
    except Exception:
        pending_users = []

    return render_template('dashboard.html', stats=stats, pending_users=pending_users)

@app.route('/approve/<int:user_id>', methods=['POST'])
def approve(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        httpx.post(f"{API_BASE_URL}/admin/approve/{user_id}", timeout=5.0)
    except Exception as e:
        flash(f"Ошибка при одобрении: {e}")
    return redirect(url_for('dashboard'))

@app.route('/reject/<int:user_id>', methods=['POST'])
def reject(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    try:
        httpx.post(f"{API_BASE_URL}/admin/reject/{user_id}", timeout=5.0)
    except Exception as e:
        flash(f"Ошибка при отклонении: {e}")
    return redirect(url_for('dashboard'))

@app.route('/alumni')
def alumni():
    if not session.get('logged_in'):
        return redirect(url_for('index'))
    conn = get_db_connection()
    students = conn.execute('''
        SELECT u.full_name, u.faculty, u.graduation_year, u.status, e.company_name, e.position_level 
        FROM users u 
        LEFT JOIN employment e ON u.telegram_id = e.user_id AND e.is_current = 1
        ORDER BY u.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('alumni.html', students=students)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
