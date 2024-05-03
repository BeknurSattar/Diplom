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

def first_frame(self, camera_id):
    first_frame = None
    video = cv2.VideoCapture(camera_id)
    while True:
        frame = video.read()
        img = cv2.resize(frame, (800, 600))
        if first_frame is None:
            first_frame = img.copy()
    return first_frame

# def open_cam(self, class_id):
#     camera_id = self.camera_ids[class_id]
#     self.detectByCamera(camera_id, class_id)
#
#
# def detectByCamera(self, camera_id, class_id):
#     global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
#     max_count3 = 0
#     framex3 = []
#     county3 = []
#     max3 = []
#     avg_acc3_list = []
#     max_avg_acc3_list = []
#     max_acc3 = 0
#     max_avg_acc3 = 0
#
#     # function defined to plot the people count in camera
#
#     video = cv2.VideoCapture(camera_id)
#     odapi = DetectorAPI()
#     threshold = 0.7
#
#     x3 = 0
#     while True:
#         check, frame = video.read()
#         if not check:
#             break
#         img = cv2.resize(frame, (800, 600))
#
#         boxes, scores, classes, num = odapi.processFrame(img)
#         person = 0
#         acc = 0
#         for i in range(len(boxes)):
#             if classes[i] == 1 and scores[i] > threshold:
#                 box = boxes[i]
#                 person += 1
#                 cv2.rectangle(img, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)  # cv2.FILLED
#                 cv2.putText(img, f'P{person, round(scores[i], 2)}', (box[1] - 30, box[0] - 8),
#                             cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)  # (75,0,130),
#                 acc += scores[i]
#                 if (scores[i] > max_acc3):
#                     max_acc3 = scores[i]
#
#         if (person > max_count3):
#             max_count3 = person
#
#         # if writer is not None:
#         #     writer.write(img)
#
#         cv2.imshow("Analiz", img)
#         key = cv2.waitKey(1)
#         if key & 0xFF == ord('q'):
#             # Функция остановки таймера
#             stop_periodic_data_insert()
#             break
#
#         county3.append(person)
#         x3 += 1
#         framex3.append(x3)
#         if (person >= 1):
#             avg_acc3_list.append(acc / person)
#             if ((acc / person) > max_avg_acc3):
#                 max_avg_acc3 = (acc / person)
#         else:
#             avg_acc3_list.append(acc)
#
#         start_periodic_data_insert(person, class_id)
#
#     video.release()
#
#     def cam_enumeration_plot():
#         plt.figure(facecolor='orange', )
#         ax = plt.axes()
#         ax.set_facecolor("yellow")
#         plt.plot(framex3, county3, label="Human Count", color="green", marker='o', markerfacecolor='blue')
#         plt.plot(framex3, max3, label="Max. Human Count", linestyle='dashed', color='fuchsia')
#         plt.xlabel('Time (sec)')
#         plt.ylabel('Human Count')
#         plt.legend()
#         plt.title("Enumeration Plot")
#         plt.show()
#
#     def cam_accuracy_plot():
#         plt.figure(facecolor='orange', )
#         ax = plt.axes()
#         ax.set_facecolor("yellow")
#         plt.plot(framex3, avg_acc3_list, label="Avg. Accuracy", color="green", marker='o', markerfacecolor='blue')
#         plt.plot(framex3, max_avg_acc3_list, label="Max. Avg. Accuracy", linestyle='dashed', color='fuchsia')
#         plt.xlabel('Time (sec)')
#         plt.ylabel('Avg. Accuracy')
#         plt.title('Avg. Accuracy Plot')
#         plt.legend()
#         plt.show()
#
#     def cam_gen_report():
#         pdf = FPDF(orientation='P', unit='mm', format='A4')
#         pdf.add_page()
#         pdf.set_font("Arial", "", 20)
#         pdf.set_text_color(128, 0, 0)
#         pdf.image('Images/eyeee.png', x=0, y=0, w=210, h=297)
#
#         pdf.text(125, 150, str(max_count3))
#         pdf.text(105, 163, str(max_acc3))
#         pdf.text(125, 175, str(max_avg_acc3))
#         if (max_count3 > 25):
#             pdf.text(26, 220, "Max. Human Detected is greater than MAX LIMIT.")
#             pdf.text(70, 235, "Region is Crowded.")
#         else:
#             pdf.text(26, 220, "Max. Human Detected is in range of MAX LIMIT.")
#             pdf.text(65, 235, "Region is not Crowded.")
#
#         pdf.output('Crowd_Report.pdf')
#
#     for i in range(len(framex3)):
#         max3.append(max_count3)
#         max_avg_acc3_list.append(max_avg_acc3)
#
#     # enumeration_button = TextButton(text="Enumeration\nPlot", on_click=lambda e: cam_enumeration_plot())
#     # self.content.controls.append(enumeration_button)
#     #
#     # avga_button = TextButton(text="Avg. Accuracy\nPlot", on_click=lambda e: cam_accuracy_plot())
#     # self.content.controls.append(avga_button)
#     #
#     # generate_button = TextButton(text="Generate  Crowd  Report", on_click=lambda e: cam_gen_report())
#     # self.content.controls.append(generate_button)
#     #
#     # back_button = TextButton(text="Back to menu", on_click=lambda e: self.back_to_menu())
#     # self.content.controls.append(back_button)
#
#     self.content.update()
