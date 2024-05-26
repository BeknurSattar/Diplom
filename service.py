# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from datetime import datetime
from Helps.utils import *

app = Flask(__name__)
CORS(app)


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return jsonify({"user_id": user[0], "authenticated": True}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

@app.route('/save_session', methods=['POST'])
def save_session():
    data = request.json
    user_id = data.get('user_id')
    authenticated = data.get('authenticated')
    language = data.get('language')
    last_access = datetime.now()
    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (user_id, authenticated, language, last_access) VALUES (%s, %s, %s, %s)",
        (user_id, authenticated, language, last_access)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"message": "Session saved"}), 200

@app.route('/load_session', methods=['GET'])
def load_session():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, authenticated, language FROM sessions ORDER BY last_access DESC LIMIT 1")
    session = cur.fetchone()
    cur.close()
    conn.close()
    if session:
        return jsonify({
            "user_id": session[0],
            "authenticated": session[1],
            "language": session[2]
        }), 200
    else:
        return jsonify({"message": "No active session found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
