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

# Функция для вставки данных в базу данных
def insert_data(self, people_count, class_id):
    """Вставляет данные о количестве людей, дате обнаружения и идентификаторе класса в базу данных."""
    self.conn = None
    try:
        self.conn = self.connect_db()
        cur = self.conn.cursor()
        cur.execute("INSERT INTO occupancy (detection_date, people_count, class_id) VALUES (%s, %s, %s)",
                    (datetime.now(), people_count, class_id))
        self.conn.commit()
        cur.close()
    except Exception as error:
        print(error)
    finally:
        if self.conn is not None:
            self.conn.close()

# Установка периодического вставления данных
def start_periodic_data_insert(person, class_id, interval=30):
    """Запускает периодическое вставление данных в базу данных."""
    insert_data(person, class_id)
    data_insert_timer = threading.Timer(interval, start_periodic_data_insert, args=(person, class_id))
    data_insert_timer.start()
    return data_insert_timer

# Глобальная переменная для таймера
data_insert_timer = None

def stop_periodic_data_insert():
    global data_insert_timer
    if data_insert_timer is not None:
        data_insert_timer.cancel()

def hash_password(password):
    # Генерируем соль для хеширования
    salt = bcrypt.gensalt()
    # Создаем хеш пароля
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed

def check_password(hashed_password, user_password):
    # Проверяем, совпадает ли введенный пароль с хешированным
    return bcrypt.checkpw(user_password.encode(), hashed_password)