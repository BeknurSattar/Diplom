import psycopg2
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

def insert_data(people_count, class_id, user_id, session_start):
    """Вставляет данные о количестве людей, дате обнаружения, идентификаторе класса, идентификаторе пользователя и времени начала сессии в базу данных."""
    conn = None
    try:
        conn = connect_db()  # Предполагается, что функция connect_db() возвращает объект соединения
        if conn is None:
            raise Exception("Не удалось подключиться к базе данных.")

        cur = conn.cursor()
        # Добавляем session_start в запрос
        cur.execute("INSERT INTO occupancy (detection_date, people_count, class_id, user_id, session_start) VALUES (%s, %s, %s, %s, %s)",
                    (datetime.now(), people_count, class_id, user_id, session_start))
        conn.commit()
        cur.close()
        print("Данные успешно вставлены.")
    except Exception as error:
        print("Ошибка вставки данных: ", error)
        raise
    finally:
        if conn is not None:
            conn.close()

def hash_password(password):
    # Генерируем соль для хеширования
    salt = bcrypt.gensalt()
    # Создаем хеш пароля
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed

def check_password(hashed_password, user_password):
    # Проверяем, совпадает ли введенный пароль с хешированным
    return bcrypt.checkpw(user_password.encode(), hashed_password)
