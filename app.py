from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
import sqlite3
import os
import random
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ----------------

def get_db():
    return sqlite3.connect("rvdss.db")

def create_tables():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS complaints(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    message TEXT,
    file TEXT,
    status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS rewards(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    points INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS library(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    file TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
    )
    """)

    conn.commit()
    conn.close()

create_tables()

# ---------------- DEFAULT ADMIN ----------------

def create_admin():

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM admins WHERE username='admin'")
    admin = cur.fetchone()

    if not admin:
        cur.execute(
            "INSERT INTO admins(username,password) VALUES(?,?)",
            ("admin","admin123"))

    conn.commit()
    conn.close()

create_admin()

# ---------------- HOME ----------------

@app.route("/")
def home():
    text = {
        "login": "Login",
        "email": "Enter Email",
        "password": "Enter Password"
    }
    return render_template("login.html", text=text)

# ---------------- REGISTER ----------------

@app.route("/register_page")
def register_page():
    return render_template("register.html")

@app.route("/register",methods=["POST"])
def register():

    name=request.form["name"]
    email=request.form["email"]
    password=request.form["password"]

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
        "INSERT INTO users(name,email,password) VALUES(?,?,?)",
        (name,email,password))

    conn.commit()
    conn.close()

    return redirect("/")

# ---------------- LOGIN ----------------

@app.route("/login",methods=["POST"])
def login():

    email=request.form["email"]
    password=request.form["password"]

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE email=? AND password=?",
        (email,password))

    user=cur.fetchone()
    conn.close()

    if user:
        session["user"]=user[1]
        return redirect("/dashboard")
    else:
        return "Invalid Login"

# ---------------- ADMIN ----------------

@app.route("/admin")
def admin_page():
    return render_template("admin_login.html")

@app.route("/admin_login",methods=["POST"])
def admin_login():

    username=request.form["username"]
    password=request.form["password"]

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
        "SELECT * FROM admins WHERE username=? AND password=?",
        (username,password))

    admin=cur.fetchone()
    conn.close()

    if admin:
        session["admin"]=username
        return redirect("/admin_dashboard")
    else:
        return "Invalid Admin"

@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin")

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints")
    complaints=cur.fetchone()[0]

    cur.execute("SELECT user,points FROM rewards ORDER BY points DESC")
    leaderboard=cur.fetchall()

    conn.close()

    return render_template(
        "admin_dashboard.html",
        users=users,
        complaints=complaints,
        leaderboard=leaderboard)

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin",None)
    return redirect("/admin")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user" not in session:
        return redirect("/")

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT COUNT(*) FROM complaints")
    complaints=cur.fetchone()[0]

    cur.execute("SELECT status, COUNT(*) FROM complaints GROUP BY status")
    status_data=cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM alerts")
    alerts=cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM library")
    books=cur.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        user=session["user"],
        complaints=complaints,
        alerts=alerts,
        books=books,
        status_data=status_data
    )

# ---------------- FILE ----------------

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"],filename)

# ---------------- COMPLAINT ----------------

@app.route("/complaint_page")
def complaint_page():

    if "user" not in session:
        return redirect("/")

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT * FROM complaints WHERE user=?", (session["user"],))
    complaints=cur.fetchall()

    conn.close()

    return render_template("complaints.html",complaints=complaints)

@app.route("/complaints")
def complaints_redirect():
    return redirect("/complaint_page")

@app.route("/complaint",methods=["POST"])
def complaint():

    if "user" not in session:
        return redirect("/")

    message=request.form["message"]
    user=session["user"]

    file=request.files["file"]
    filename=""

    if file and file.filename!="":
        filename=secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"],filename))

    conn=get_db()
    cur=conn.cursor()

    cur.execute(
        "INSERT INTO complaints(user,message,file,status) VALUES(?,?,?,?)",
        (user,message,filename,"Pending"))

    # Notification
    cur.execute(
        "INSERT INTO alerts(message) VALUES(?)",
        (f"New complaint by {user}",)
    )

    # Rewards
    cur.execute("SELECT * FROM rewards WHERE user=?", (user,))
    data=cur.fetchone()

    if data:
        cur.execute("UPDATE rewards SET points=points+10 WHERE user=?", (user,))
    else:
        cur.execute("INSERT INTO rewards(user,points) VALUES(?,?)", (user,10))

    conn.commit()
    conn.close()

    return redirect("/complaint_page")

# ---------------- REWARDS ----------------

@app.route("/rewards")
def rewards():

    if "user" not in session:
        return redirect("/")

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT points FROM rewards WHERE user=?", (session["user"],))
    data=cur.fetchone()
    points=data[0] if data else 0

    cur.execute("SELECT user,points FROM rewards ORDER BY points DESC")
    leaderboard=cur.fetchall()

    conn.close()

    return render_template("rewards.html",points=points,leaderboard=leaderboard)

# ---------------- NOTIFICATIONS ----------------

@app.route("/notifications")
def notifications():

    if "user" not in session:
        return redirect("/")

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT * FROM alerts ORDER BY id DESC")
    data=cur.fetchall()

    conn.close()

    return render_template("notifications.html",notifications=data)

# ---------------- CHATBOT ----------------

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():

    if "user" not in session:
        return redirect("/")

    reply = ""

    if request.method == "POST":
        msg = request.form["message"].lower()

        if "hi" in msg or "hello" in msg:
            reply = "👋 Hello! How can I help you?"

        elif "complaint" in msg:
            reply = "📢 You can register complaints in the Complaint section."

        elif "water" in msg:
            reply = "💧 Please conserve water. Visit Water section for tips."

        elif "health" in msg:
            reply = "🏥 Stay healthy! Eat well and exercise daily."

        elif "education" in msg:
            reply = "📚 Study regularly and check Education section."

        elif "job" in msg:
            reply = "💼 Jobs will be available soon in the Jobs section."

        elif "scheme" in msg:
            reply = "📄 Check Government Schemes section for benefits."

        else:
            reply = "🤖 I am still learning... please try another question."

    return render_template("chatbot.html", reply=reply)

# ---------------- MAP ----------------

@app.route("/map")
def map_view():
    return render_template("map.html")

# ---------------- OTHER ----------------

@app.route("/agriculture")
def agriculture():
    return render_template("agriculture.html")

@app.route("/health")
def health():
    return render_template("health.html")

@app.route("/education")
def education():
    return render_template("education.html")

@app.route("/water")
def water():
    return render_template("water.html")

@app.route("/alerts")
def alerts():
    conn=get_db()
    cur=conn.cursor()
    cur.execute("SELECT * FROM alerts")
    alerts=cur.fetchall()
    conn.close()
    return render_template("alerts.html",alerts=alerts)

@app.route("/library")
def library():
    conn=get_db()
    cur=conn.cursor()
    cur.execute("SELECT * FROM library")
    books=cur.fetchall()
    conn.close()
    return render_template("library.html",books=books)

@app.route("/profile")
def profile():

    if "user" not in session:
        return redirect("/")

    conn=get_db()
    cur=conn.cursor()

    cur.execute("SELECT * FROM users WHERE name=?", (session["user"],))
    user=cur.fetchone()

    conn.close()

    return render_template("profile.html",user=user)

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------

if __name__=="__main__":
    app.run(debug=True)