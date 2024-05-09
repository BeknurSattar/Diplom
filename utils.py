import cv2
import psycopg2
from datetime import datetime
import threading
import bcrypt

from persondetection import DetectorAPI


# Функция подключения к базе данных
def connect_db():
    try:
        conn = psycopg2.connect(
            dbname="Class",
            user="postgres",
            password="beknur32",
            host="localhost"
        )
        return conn
    except psycopg2.OperationalError as e:
        print("Ошибка подключения к базе данных: ", e)
        return None

data_insert_timer = None
# Функция для вставки данных в базу данных
def insert_data(people_count, class_id):
    """Вставляет данные о количестве людей, дате обнаружения и идентификаторе класса в базу данных."""
    conn = None
    try:
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO occupancy (detection_date, people_count, class_id) VALUES (%s, %s, %s)",
                    (datetime.now(), people_count, class_id))
        conn.commit()
        cur.close()
    except Exception as error:
        print("Ошибка вставки данных: ", error)
    finally:
        if conn is not None:
            conn.close()

# Установка периодического вставления данных
def start_periodic_data_insert(person, class_id, interval=5000):
    """Запускает периодическое вставление данных в базу данных."""
    global data_insert_timer

    # Останавливаем предыдущий таймер, если он существует
    if data_insert_timer is not None:
        data_insert_timer.cancel()

    # Вставляем данные
    insert_data(person, class_id)

    # Запускаем таймер снова
    data_insert_timer = threading.Timer(interval / 1000.0, start_periodic_data_insert, args=(person, class_id, interval))
    data_insert_timer.start()

def stop_periodic_data_insert():
    global data_insert_timer
    if data_insert_timer is not None:
        data_insert_timer.cancel()
        data_insert_timer = None
def hash_password(password):
    # Генерируем соль для хеширования
    salt = bcrypt.gensalt()
    # Создаем хеш пароля
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed

def check_password(hashed_password, user_password):
    # Проверяем, совпадает ли введенный пароль с хешированным
    return bcrypt.checkpw(user_password.encode(), hashed_password)

def get_user_position_id(self):
    """Получение ID должности пользователя из базы данных."""
    if self.user_id is None:
        print("user_id не установлен.")
        return None

    position_id = None
    try:
        conn = connect_db()
        if conn is None:
            print("Не удалось подключиться к базе данных.")
            return None

        cursor = conn.cursor()
        cursor.execute("SELECT position_id FROM users WHERE user_id = %s;", (self.user_id,))
        result = cursor.fetchone()
        if result:
            position_id = result[0]
        else:
            print(f"Не найден position_id для user_id {self.user_id}.")
        cursor.close()
    except Exception as e:
        print(f"Ошибка при получении ID должности: {e}")
    finally:
        if conn:
            conn.close()

    return position_id
def first_frame(self, camera_id):
    first_frame = None
    video = cv2.VideoCapture(camera_id)
    while True:
        frame = video.read()
        img = cv2.resize(frame, (800, 600))
        if first_frame is None:
            first_frame = img.copy()
    return first_frame




