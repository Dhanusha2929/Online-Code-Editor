from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this in production!

DATABASE = 'users.db'

# --- SQLite Connection Helper ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

# --- Initialize DB if it doesn't exist ---
def init_db():
    if not os.path.exists(DATABASE):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            );
        ''')
        conn.commit()
        cursor.close()
        conn.close()

# --- Home: Route logic for new/known user ---
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('welcome'))
    return redirect(url_for('signup'))

# --- Signup page & form handling ---
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname'].strip()
        lastname = request.form['lastname'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']  # In production, hash this!
        if not (firstname and lastname and email and password):
            error = "All fields are required."
            return render_template('signup.html', error=error)
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (firstname, lastname, email, password) VALUES (?, ?, ?, ?)", 
                           (firstname, lastname, email, password))
            conn.commit()
            session['user'] = email
            return redirect(url_for('welcome'))
        except sqlite3.IntegrityError:
            error = "Email already exists or signup error. Try logging in."
            return render_template('signup.html', error=error)
        finally:
            cursor.close()
            conn.close()
    return render_template('signup.html')

# --- Login page & form handling ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if not (email and password):
            error = "Both email and password are required."
            return render_template('login.html', error=error)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['user'] = email
            return redirect(url_for('welcome'))
        else:
            error = "Invalid credentials. Try again."
            return render_template('login.html', error=error)
    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# --- Welcome page (redirect if not logged in) ---
@app.route('/welcome')
def welcome():
    if 'user' not in session:
        return redirect(url_for('signup'))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT firstname FROM users WHERE email=?", (session['user'],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('welcome.html', firstname=user['firstname'] if user else 'User')

# --- Coding page ---
@app.route('/coding')
def coding():
    if 'user' not in session:
        return redirect(url_for('signup'))
    return render_template('coding.html')

# --- Lessons page ---
@app.route('/lessons')
def lessons():
    if 'user' not in session:
        return redirect(url_for('signup'))
    return render_template('lessons.html')

# --- Sample Projects page ---
@app.route('/samples')
def samples():
    if 'user' not in session:
        return redirect(url_for('signup'))
    return render_template('sample-projects.html')

# --- 404 Error Handler (optional) ---
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

# --- Run App ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)