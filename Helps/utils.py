import cv2
import psycopg2
from datetime import datetime
import threading
import bcrypt


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
from datetime import datetime

def insert_data(people_count, class_id, user_id):
    """Вставляет данные о количестве людей, дате обнаружения, идентификаторе класса и идентификаторе пользователя в базу данных."""
    conn = None
    try:
        conn = connect_db()  # Предполагается, что функция connect_db() возвращает объект соединения
        if conn is None:
            raise Exception("Не удалось подключиться к базе данных.")

        cur = conn.cursor()
        # Добавляем user_id в запрос
        cur.execute("INSERT INTO occupancy (detection_date, people_count, class_id, user_id) VALUES (%s, %s, %s, %s)",
                    (datetime.now(), people_count, class_id, user_id))
        conn.commit()
        cur.close()
        print("Данные успешно вставлены.")
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





