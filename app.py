from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_TO_SOMETHING_RANDOM"   # Step 1: Required for sessions

# Set your admin password here
ADMIN_PASSWORD = "yourpasswordhere"


# ---------------------------
# Admin Login Route (Step 2)
# ---------------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('admin_login.html', error="Invalid password")

    return render_template('admin_login.html')


# ---------------------------
# Protected Admin Page (Step 3)
# ---------------------------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html')


# ---------------------------
# Your Existing Routes Below
# ---------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/raffle')
def raffle():
    conn = sqlite3.connect('raffle.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_path FROM entries")
    entries = cursor.fetchall()
    conn.close()
    return render_template('raffle.html', entries=entries)


@app.route('/winner/<int:id>')
def winner(id):
    conn = sqlite3.connect('raffle.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, image_path FROM entries WHERE id=?", (id,))
    entry = cursor.fetchone()
    conn.close()
    return render_template('winner.html', entry=entry)


@app.route('/admin-logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
