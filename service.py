# server.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from Helps.utils import *
import psycopg2
from detection.persondetection import DetectorAPI
import bcrypt
import os
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)

model_path = os.path.abspath('runs/detect/train2/weights/best.pt')
detector = DetectorAPI(model_path=model_path)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    try:
        data = request.json
        image_data = data['frame']
        image = Image.open(BytesIO(base64.b64decode(image_data)))
        image = np.array(image)

        # Обработка кадра
        boxes, scores, classes, num = detector.processFrame(image)

        result = {
            'boxes': boxes,
            'scores': scores,
            'classes': classes,
            'num': num
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
#--------------------------------------------------------------------------------------------------
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
#--------------------------------------------------------------------------------------

@app.route('/total_people', methods=['GET'])
def total_people():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT SUM(people_count) FROM occupancy WHERE user_id = %s", (user_id,))
                total_people = cur.fetchone()[0]
            return jsonify({"total_people": total_people if total_people else 0}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/latest_graphs', methods=['GET'])
def latest_graphs():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT graph_type_id, MAX(session_start) as last_session_start
                    FROM graphs
                    WHERE user_id = %s
                    GROUP BY graph_type_id
                """, (user_id,))
                latest_sessions = cur.fetchall()
                graph_paths = []
                for graph_type_id, last_session_start in latest_sessions:
                    cur.execute("""
                        SELECT graph_path FROM graphs
                        WHERE graph_type_id = %s AND session_start = %s AND user_id = %s;
                    """, (graph_type_id, last_session_start, user_id))
                    result = cur.fetchone()
                    if result:
                        graph_paths.append(result[0])
                return jsonify({"graph_paths": graph_paths}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/latest_data', methods=['GET'])
def latest_data():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT class_id, MAX(people_count) FROM occupancy
                    WHERE user_id = %s
                    GROUP BY class_id
                    ORDER BY class_id
                """, (user_id,))
                data = cur.fetchall()
            return jsonify({"data": data}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500
#-----------------------------------------------------------------------------------------

@app.route('/get_user_profile', methods=['GET'])
def get_user_profile():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.username, u.email, p.title as position, u.image_path
                    FROM users u
                    JOIN positions p ON u.position_id = p.id
                    WHERE u.user_id = %s
                """, (user_id,))
                user_info = cur.fetchone()
            if user_info:
                return jsonify({
                    "username": user_info[0],
                    "email": user_info[1],
                    "position": user_info[2],
                    "image_path": user_info[3]
                }), 200
            else:
                return jsonify({"error": "User not found"}), 404
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/update_password', methods=['POST'])
def update_password():
    data = request.json
    user_id = data.get('user_id')
    new_password = data.get('new_password')
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET password = %s WHERE user_id = %s", (hashed_password, user_id))
                conn.commit()
            return jsonify({"message": "Password successfully updated"}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/update_profile', methods=['POST'])
def update_profile():
    data = request.json
    user_id = data.get('user_id')
    new_username = data.get('new_username')
    new_email = data.get('new_email')
    image_path = data.get('image_path')

    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE users SET username = %s, email = %s, image_path = %s WHERE user_id = %s",
                            (new_username, new_email, image_path, user_id))
                conn.commit()
            return jsonify({"message": "Profile successfully updated"}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500
#---------------------------------------------------------------------------------------------------------
@app.route('/get_class_data', methods=['GET'])
def get_class_data():
    user_id = request.args.get('user_id')
    class_id = request.args.get('class_id')

    if not user_id or not class_id:
        return jsonify({"error": "Invalid request parameters"}), 400

    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Получение времени начала последней сессии
                cur.execute(
                    "SELECT MAX(session_start) FROM occupancy WHERE class_id = %s AND user_id = %s;",
                    (class_id, user_id))
                last_session_start = cur.fetchone()[0]

                if last_session_start is None:
                    return jsonify({"data": []}), 200

                # Запрос данных о последних 10 детекциях по class_id
                cur.execute(
                    "SELECT detection_date, people_count FROM occupancy WHERE class_id = %s AND user_id = %s AND session_start = %s",
                    (class_id, user_id, last_session_start))
                rows = cur.fetchall()

                # Преобразование данных в список словарей и форматирование даты
                data = [{"detection_date": row[0].strftime("%a, %d %b %Y %H:%M:%S GMT"), "people_count": row[1]} for row
                        in rows]

            return jsonify({"data": data}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/get_graph_path', methods=['GET'])
def get_graph_path():
    user_id = request.args.get('user_id')
    class_id = request.args.get('class_id')
    graph_number = request.args.get('graph_number')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(session_start) FROM graphs
                    WHERE class_id = %s AND graph_type_id = %s AND user_id = %s;
                """, (class_id, graph_number, user_id))
                last_session_start = cur.fetchone()[0]

                if last_session_start:
                    cur.execute("""
                        SELECT graph_path FROM graphs
                        WHERE class_id = %s AND graph_type_id = %s AND session_start = %s AND user_id = %s;
                    """, (class_id, graph_number, last_session_start, user_id))
                    result = cur.fetchone()
                    if result:
                        return jsonify({"graph_path": result[0]}), 200
                    else:
                        return jsonify({"error": "Graph not found"}), 404
                else:
                    return jsonify({"error": "No recent sessions"}), 404
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/get_user_details', methods=['GET'])
def get_user_details():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.username, p.title
                    FROM users u
                    JOIN positions p ON u.position_id = p.id
                    WHERE u.user_id = %s
                """, (user_id,))
                result = cur.fetchone()
            if result:
                return jsonify({
                    "username": result[0],
                    "position": result[1]
                }), 200
            else:
                return jsonify({"error": "User not found"}), 404
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/get_class_ids', methods=['GET'])
def get_class_ids():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT o.class_id 
                    FROM occupancy o
                    JOIN camera_permissions cp ON o.class_id = cp.camera_id
                    WHERE cp.position_id = (SELECT position_id FROM users WHERE user_id = %s)
                    ORDER BY o.class_id;
                """, (user_id,))
                class_ids = cur.fetchall()
            return jsonify({"class_ids": [cid[0] for cid in class_ids]}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500
#-------------------------------------------------------------------------------------------------------
@app.route('/get_user_position_id', methods=['GET'])
def get_user_position_id():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT position_id FROM users WHERE user_id = %s;", (user_id,))
                result = cur.fetchone()
            if result:
                return jsonify({"position_id": result[0]}), 200
            else:
                return jsonify({"error": "User not found"}), 404
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/get_video_files_for_user', methods=['GET'])
def get_video_files_for_user():
    position_id = request.args.get('position_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT c.id, c.path
                    FROM cameras c
                    JOIN camera_permissions cp ON c.id = cp.camera_id
                    WHERE cp.position_id = %s;
                """, (position_id,))
                video_files = cur.fetchall()
            return jsonify({"video_files": [{"id": row[0], "path": row[1]} for row in video_files]}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/insert_data', methods=['POST'])
def insert_data():
    data = request.json
    detected_people = data.get('detected_people')
    class_id = data.get('class_id')
    user_id = data.get('user_id')
    session_start_str = data.get('session_start')
    session_start = datetime.fromisoformat(session_start_str)  # Преобразование строки в datetime
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO occupancy (detection_date, people_count, class_id, user_id, session_start) VALUES (%s, %s, %s, %s, %s)",
                    (datetime.now(), detected_people, class_id, user_id, session_start))
                conn.commit()
            return jsonify({"message": "Data inserted successfully"}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500
@app.route('/get_graph_types', methods=['GET'])
def get_graph_types():
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, type_name FROM graph_types;")
                graph_types = cur.fetchall()
            return jsonify({"graph_types": [{"id": row[0], "type_name": row[1]} for row in graph_types]}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/save_graph_info', methods=['POST'])
def save_graph_info():
    data = request.json
    user_id = data.get('user_id')
    class_id = data.get('class_id')
    graph_type_id = data.get('graph_type_id')
    graph_path = data.get('graph_path')
    session_start_str = data.get('session_start')
    session_start = datetime.fromisoformat(session_start_str)  # Преобразование строки в datetime
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO graphs (user_id, class_id, graph_type_id, graph_path, upload_date, session_start) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, class_id, graph_type_id, graph_path, datetime.now(), session_start))
                conn.commit()
            return jsonify({"message": "Graph info saved successfully"}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500
#-------------------------------------------------------------------------------------------------------
@app.route('/get_user_settings', methods=['GET'])
def get_user_settings():
    user_id = request.args.get('user_id')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT theme, language FROM user_settings WHERE user_id = %s;", (user_id,))
                result = cur.fetchone()
            if result:
                return jsonify({"theme": result[0], "language": result[1]}), 200
            else:
                return jsonify({"error": "Settings not found"}), 404
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500

@app.route('/update_user_settings', methods=['POST'])
def update_user_settings():
    data = request.json
    user_id = data.get('user_id')
    theme = data.get('theme')
    language = data.get('language')
    conn = connect_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE user_settings SET theme = %s, language = %s WHERE user_id = %s",
                    (theme, language, user_id))
                conn.commit()
            return jsonify({"message": "Settings updated successfully"}), 200
        except psycopg2.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    else:
        return jsonify({"error": "Database connection failed"}), 500
#--------------------------------------------------------------------------------------------------
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, password FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                user_id, hashed_password = user
                if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
                    return jsonify({'user_id': user_id}), 200
                else:
                    return jsonify({'error': 'Incorrect password'}), 401
            else:
                return jsonify({'error': 'User not found'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Failed to connect to the database'}), 500

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    position_title = data.get('position_title')

    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM positions WHERE title = %s", (position_title,))
            position_id = cursor.fetchone()
            if not position_id:
                return jsonify({'error': 'Invalid position title'}), 400

            cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE email = %s)", (email,))
            if cursor.fetchone()[0]:
                return jsonify({'error': 'Email already in use'}), 400

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute("INSERT INTO users (username, email, password, position_id) VALUES (%s, %s, %s, %s)",
                           (username, email, hashed_password, position_id[0]))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'message': 'Registration completed'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Failed to connect to the database'}), 500
@app.route('/api/positions', methods=['GET'])
def api_get_positions():
    conn = connect_db()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM positions ORDER BY title")
            positions = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({'positions': positions}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Failed to connect to the database'}), 500
#--------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
