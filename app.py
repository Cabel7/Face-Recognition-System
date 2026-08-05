from flask import Flask, render_template, request, session, redirect, url_for
from utils.face_encoder import encode_faces
from utils.recognizer import recognize_from_frame
import base64, os
import numpy as np
import cv2
import sqlite3
import time
from utils.capture import capture_face



app = Flask(__name__)

app.secret_key = "secret123"

# ------------------ DATABASE INIT ------------------

def init_db():
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT UNIQUE,
        role TEXT,
        password TEXT
    )
    """)

    # Attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        user_id INTEGER,
        date TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()


# ------------------ HOME ------------------

@app.route("/")
def index():
    return render_template("index.html")

# ------------------ USER REGISTER ------------------

@app.route("/register_user", methods=["GET", "POST"])
def register_user():

    if request.method == "POST":
        name = request.form.get("name").strip()
        username = request.form.get("username").strip().lower()
        password = request.form.get("password")
        role = request.form.get("role")

        if not name or not password or not role:
            return "All fields required"

        conn = sqlite3.connect("database/database.db")
        cursor = conn.cursor()

        # Prevent duplicate user
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))        
        if cursor.fetchone():
            conn.close()
            return "Username already exists"

        cursor.execute(
            "INSERT INTO users (name, username, role, password) VALUES (?, ?, ?, ?)",
            (name, username, role, password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register_user.html")


# ------------------ LOGIN ------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    #  already logged in → don't allow login page
    if "user" in session:
        return redirect(f"/dashboard/{session['user']}")

    if request.method == "POST":
        username = request.form.get("username").strip().lower()
        password = request.form.get("password")

        conn = sqlite3.connect("database/database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]     # username
            session["user_id"] = user[0]
            session["role"] = user[2]
            return redirect(f"/dashboard/{user[1]}")

        return "Invalid Credentials"

    return render_template("login.html")


#--------Logout----------


@app.route("/logout")
def logout():
    session.clear()   
    return redirect("/")



@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ------------------ DASHBOARD ------------------

@app.route("/dashboard/<username>")
def dashboard(username):

    if "user" not in session:
        return redirect("/login")

    if session["user"] != username:
        return "Unauthorized", 403

    return render_template("dashboard.html", name=username)


# ------------------ ENCODE ------------------

@app.route("/encode")
def encode():
    encode_faces()
    return "<h3>Encoding Done! Now go to /start</h3>"


# ------------------ START ATTENDANCE ------------------

@app.route("/start", methods=["POST"])
def start():

    if not os.path.exists("encodings/encodings.pickle"):
        encode_faces()

    data = request.get_json()
    image_data = data["image"]

    #  Decode image from browser
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    #  USE THIS (correct function)
    detected_name = recognize_from_frame(frame)

    if not detected_name:
        return {"status": "error", "message": "Not Recognised"}
    

    # CASE 1: User is LOGGED IN
    if "user" in session:

        # If face doesn't match account → block
        if detected_name.strip().lower() != session["user"].strip().lower():
            return {"status": "error", "message": "Face does NOT match logged-in user"}

        name_to_mark = session["user"]

    # CASE 2: Public (no login)
    else:
        name_to_mark = detected_name

    # Mark attendance
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username FROM users WHERE username=?",
        (name_to_mark,)
    )
    user = cursor.fetchone()

    if not user:
        return {"status": "error", "message": "User not found"}

    user_id = user[0]

    # Prevent duplicate
    cursor.execute(
        "SELECT * FROM attendance WHERE user_id=? AND date=date('now')",
        (user_id,)
    )
    exists = cursor.fetchone()

    if exists:
        return {"status": "info", "message": f"{name_to_mark} already marked"}

    cursor.execute(
        "INSERT INTO attendance (user_id, date, time) VALUES (?, date('now'), time('now'))",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return {"status": "success", "message": f"Attendance marked for {detected_name}"}


# ------------------ VIEW ATTENDANCE ------------------

@app.route("/attendance")
def attendance():

    if "user" not in session:
        return redirect("/login")

    role = session.get("role")   # GET ROLE FROM SESSION

    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT u.name, a.date, a.time
    FROM attendance a
    JOIN users u ON a.user_id = u.id
    WHERE u.role = ?
    """, (role,))

    data = cursor.fetchall()
    conn.close()

    return render_template("attendance.html", data=data)


# ------------------ FACE REGISTER ------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        name = request.form.get("name")

        if not name:
            return "Name required"

        success = capture_face(name)

        if success:
            return "Face captured successfully. Now go to /encode"
        else:
            return "Capture failed"

    return render_template("register.html")


#----------camera-----------

@app.route("/capture_face", methods=["POST"])
def capture_face_api():

    data = request.get_json()

    image_data = data["image"]
    name = data["name"]

    # Create folder if not exists
    user_dir = f"dataset/{name.lower()}"
    os.makedirs(user_dir, exist_ok=True)

    

    filename = str(int(time.time() * 1000))
    path = f"{user_dir}/{filename}.jpg"

    # Decode base64
    image_data = image_data.split(",")[1]
    image_bytes = base64.b64decode(image_data)

    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    
    cv2.imwrite(path, frame)

    print("Saving image for:", name)
    print("Path:", path)

    print("Files in folder:", len(os.listdir(user_dir)))

    encode_faces()   # ALWAYS RUN

    return f"Saved image for {name}"

# ------------------ ADMIN ------------------

@app.route("/admin", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        key = request.form.get("key")

        if key == "admin123":
            session["admin"] = True 
            return redirect("/admin_panel")

        return "Wrong Password"

    return """
    <h2>Admin Login</h2>
    <form method="POST">
        Password: <input type="password" name="key">
        <button type="submit">Login</button>
    </form>
    """

@app.route("/admin_panel")
def admin_panel():

    if not session.get("admin"):
        return redirect("/admin")
    
    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT a.rowid, u.name, u.role, a.date, a.time
    FROM attendance a
    JOIN users u ON a.user_id = u.id
    """)
    data = cursor.fetchall()

    conn.close()

    return render_template("admin.html", data=data)

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/")

#--------------------Admin_Action--------------

@app.route("/delete/<int:id>")
def delete(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM attendance WHERE rowid=?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin_panel")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        date = request.form.get("date")
        time = request.form.get("time")

        cursor.execute(
            "UPDATE attendance SET date=?, time=? WHERE rowid=?",
            (date, time, id)
        )

        conn.commit()
        conn.close()

        return redirect("/admin_panel")

    # GET → fetch existing data
    cursor.execute("SELECT date, time FROM attendance WHERE rowid=?", (id,))
    data = cursor.fetchone()

    conn.close()

    return render_template("edit.html", data=data, id=id)


@app.route("/add_attendance", methods=["GET", "POST"])
def add_attendance():

    if not session.get("admin"):
        return redirect("/admin")

    conn = sqlite3.connect("database/database.db")
    cursor = conn.cursor()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        date = request.form.get("date")
        time = request.form.get("time")

        cursor.execute(
            "INSERT INTO attendance (user_id, date, time) VALUES (?, ?, ?)",
            (user_id, date, time)
        )

        conn.commit()
        conn.close()

        return redirect("/admin_panel")

    # Load users for dropdown
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()

    conn.close()

    return render_template("add_attendance.html", users=users)

# ------------------ RUN APP ------------------

if __name__ == "__main__":
    init_db()
    app.run()
