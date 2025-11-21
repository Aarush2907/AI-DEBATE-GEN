import os
import pathlib
import sqlite3
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from dotenv import load_dotenv
from openai import OpenAI

# ===============================
# Load environment variables
# ===============================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ===============================
# Flask App
# ===============================
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Temp directory for audio files
BASE_DIR = pathlib.Path(__file__).resolve().parent
TMP_DIR = BASE_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

# Database Helper
def get_db_connection():
    conn = sqlite3.connect('LoginData.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def login_page():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    conn.close()
    
    if user:
        session['user'] = user['email']
        return redirect(url_for('dashboard'))
    else:
        flash("Wrong email or password")
        return redirect(url_for('login_page'))

@app.route("/signup", methods=["POST"])
def signup():
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = request.form.get("password")
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)',
                     (first_name, last_name, email, password))
        conn.commit()
        conn.close()
        session['user'] = email
        return redirect(url_for('dashboard'))
    except sqlite3.IntegrityError:
        conn.close()
        flash("Email already exists")
        return redirect(url_for('login_page'))

@app.route("/dashboard")
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    
    email = session['user']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    
    first_name = user['first_name'] if user else "User"
    last_name = user['last_name']    if user else "User"
    
    return render_template("dashboard.html", first_name=first_name, last_name=last_name)

@app.route("/logout")
def logout():
    session.pop('user', None)
    return redirect(url_for('login_page'))

@app.route("/api/listen", methods=["POST"])
def listen():
    """
    Accepts multipart/form-data audio file from recorder.js,
    saves it as temp_audio.webm,
    sends to OpenAI Whisper API,
    prints transcription,
    returns JSON with text.
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio = request.files["audio"]

    # Save temporary file
    temp_path = TMP_DIR / "temp_audio.webm"
    audio.save(temp_path)

    transcription_text = ""

    try:
        # --- Transcribe using OpenAI ---
        with open(temp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",  # OpenAI’s STT model
                file=f
            )

        transcription_text = result.text

        print("\n===== TRANSCRIPTION =====")
        print(transcription_text)
        print("=========================\n")

    except Exception as e:
        print("Error during transcription:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        # Delete temp file
        try:
            temp_path.unlink(missing_ok=True)
        except:
            pass

    return jsonify({
        "ok": True,
        "transcript": transcription_text
    })

if __name__ == "__main__":
    app.run(debug=True)
