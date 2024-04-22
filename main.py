import threading
from tkinter import *
import tkinter as tk
import tkinter.messagebox as mbox
from tkinter import font as tkfont
import cv2
from persondetection import DetectorAPI
import matplotlib.pyplot as plt
from fpdf import FPDF
import psycopg2
from datetime import datetime


def connect_db():
    """Подключение к базе данных PostgreSQL. Возвращает объект соединения."""
    conn = psycopg2.connect(
        dbname="Class",
        user="postgres",
        password="beknur32",
        host="localhost"
    )
    return conn

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
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# Словарь, сопоставляющий классы с идентификаторами камер
camera_ids = {
    1: 0,  # Камера для класса 1
    2: 'Videoes/unihub.mp4',  # Камера для класса 2
    # Добавьте больше классов и камер по мере необходимости
}

# Глобальная переменная для таймера
data_insert_timer = None

def stop_periodic_data_insert():
    global data_insert_timer
    if data_insert_timer is not None:
        data_insert_timer.cancel()

# Main Window & Configuration
window = tk.Tk()
window.title("Analysis of class occupancy using computer vision methods")
window.iconbitmap('Images/eye.ico')
window.geometry('1200x800')

# Устанавливаем шрифт
custom_font = tkfont.Font(family="Roboto", size=50)

# Создаем метку с текстом
start_label = tk.Label(
    window,
    text="Analysis of class",
    font=custom_font,
    fg="black",
)
start_label.place(relx=0.5, rely=0.2, anchor="center")  # Разместить метку в середине окна

# Переменная для отслеживания состояния окна
exit1 = False

# Function to exit from the window
def exit_win():
    global exit1
    if mbox.askokcancel("Exit", "Do you want to exit?"):
        exit1 = True
        window.destroy()
# Function to clear the window and create a new layout

def clear_window():
    for widget in window.winfo_children():
        widget.destroy()

def camera_option():
    clear_window()  # Очищаем окно от предыдущих элементов

    def open_cam(class_id):
        global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
        max_count3 = 0
        framex3 = []
        county3 = []
        max3 = []
        avg_acc3_list = []
        max_avg_acc3_list = []
        max_acc3 = 0
        max_avg_acc3 = 0

        # Получаем идентификатор камеры для данного класса
        camera_id = camera_ids[class_id]

        # Настройка пути к файлу для сохранения на основе class_id
        output_path = f'output_video_class_{class_id}.avi'

        writer = None
        if output_path is not None:
            writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*'MJPG'), 10, (600, 600))

        # Теперь вызываем функцию detectByCamera без проверки args['output']
        detectByCamera(writer,camera_id, class_id)


    # function defined to detect from camera
    def detectByCamera(writer, camera_id, class_id):
        # global variable created
        global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
        max_count3 = 0
        framex3 = []
        county3 = []
        max3 = []
        avg_acc3_list = []
        max_avg_acc3_list = []
        max_acc3 = 0
        max_avg_acc3 = 0

        def periodic_data_insert(person, class_id):
            global data_insert_timer
            # Сохраняем данные в базу данных
            insert_data(person, class_id)
            # Перезапускаем таймер
            data_insert_timer = threading.Timer(30, periodic_data_insert, args=(person, class_id))
            data_insert_timer.start()



        # function defined to plot the people count in camera
        def cam_enumeration_plot():
            plt.figure(facecolor='orange', )
            ax = plt.axes()
            ax.set_facecolor("yellow")
            plt.plot(framex3, county3, label="Human Count", color="green", marker='o', markerfacecolor='blue')
            plt.plot(framex3, max3, label="Max. Human Count", linestyle='dashed', color='fuchsia')
            plt.xlabel('Time (sec)')
            plt.ylabel('Human Count')
            plt.legend()
            plt.title("Enumeration Plot")

            plt.show()

        def cam_accuracy_plot():
            plt.figure(facecolor='orange', )
            ax = plt.axes()
            ax.set_facecolor("yellow")
            plt.plot(framex3, avg_acc3_list, label="Avg. Accuracy", color="green", marker='o', markerfacecolor='blue')
            plt.plot(framex3, max_avg_acc3_list, label="Max. Avg. Accuracy", linestyle='dashed', color='fuchsia')
            plt.xlabel('Time (sec)')
            plt.ylabel('Avg. Accuracy')
            plt.title('Avg. Accuracy Plot')
            plt.legend()

            plt.show()

        def cam_gen_report():
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Arial", "", 20)
            pdf.set_text_color(128, 0, 0)
            pdf.image('Images/eyeee.png', x=0, y=0, w=210, h=297)

            pdf.text(125, 150, str(max_count3))
            pdf.text(105, 163, str(max_acc3))
            pdf.text(125, 175, str(max_avg_acc3))
            if (max_count3 > 25):
                pdf.text(26, 220, "Max. Human Detected is greater than MAX LIMIT.")
                pdf.text(70, 235, "Region is Crowded.")
            else:
                pdf.text(26, 220, "Max. Human Detected is in range of MAX LIMIT.")
                pdf.text(65, 235, "Region is not Crowded.")

            pdf.output('Crowd_Report.pdf')
            mbox.showinfo("Status", "Report Generated and Saved Successfully.", parent=window)

        video = cv2.VideoCapture(camera_id)
        odapi = DetectorAPI()
        threshold = 0.7

        x3 = 0
        while True:
            check, frame = video.read()
            img = cv2.resize(frame, (800, 600))
            boxes, scores, classes, num = odapi.processFrame(img)
            person = 0
            acc = 0
            for i in range(len(boxes)):

                if classes[i] == 1 and scores[i] > threshold:
                    box = boxes[i]
                    person += 1
                    cv2.rectangle(img, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)  # cv2.FILLED
                    cv2.putText(img, f'P{person, round(scores[i], 2)}', (box[1] - 30, box[0] - 8),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)  # (75,0,130),
                    acc += scores[i]
                    if (scores[i] > max_acc3):
                        max_acc3 = scores[i]

            if (person > max_count3):
                max_count3 = person

            if writer is not None:
                writer.write(img)

            cv2.imshow("Analiz", img)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                # Функция остановки таймера
                stop_periodic_data_insert()
                break

            county3.append(person)
            x3 += 1
            framex3.append(x3)
            if (person >= 1):
                avg_acc3_list.append(acc / person)
                if ((acc / person) > max_avg_acc3):
                    max_avg_acc3 = (acc / person)
            else:
                avg_acc3_list.append(acc)

            periodic_data_insert(person, class_id)

        video.release()

        for i in range(len(framex3)):
            max3.append(max_count3)
            max_avg_acc3_list.append(max_avg_acc3)

        Button(window, text="Enumeration\nPlot", command=cam_enumeration_plot, cursor="hand2", font=("Arial", 20),
               bg="orange", fg="blue").place(x=100, y=530)
        Button(window, text="Avg. Accuracy\nPlot", command=cam_accuracy_plot, cursor="hand2", font=("Arial", 20),
               bg="orange", fg="blue").place(x=700, y=530)
        Button(window, text="Generate  Crowd  Report", command=cam_gen_report, cursor="hand2", font=("Arial", 20),
               bg="gray", fg="blue").place(x=325, y=550)

    # Кнопка для запуска камеры
    for class_id in camera_ids:
        button = tk.Button(window, text=f"Class {class_id} Camera",
                           command=lambda cid=class_id: open_cam(cid),
                           font=("Arial", 15))
        button.pack(pady=10)

    back_button = tk.Button(window, text="Back to menu", command=start_app)
    back_button.pack(pady=20)

def show_class_data(class_id):
    clear_window()

    def fetch_and_display_data():
        conn = connect_db()
        cur = conn.cursor()
        # Используйте class_id в вашем SQL запросе для выбора данных конкретного класса
        cur.execute("SELECT detection_date, people_count FROM occupancy WHERE class_id = %s ORDER BY detection_date DESC LIMIT 10;", (class_id,))
        rows = cur.fetchall()
        display_text = f"Last 10 detections for class {class_id}:\n\n"
        for row in rows:
            display_text += f"Date: {row[0]}, Count: {row[1]}\n"
        data_label.config(text=display_text)
        cur.close()
        conn.close()

    fetch_data_button = tk.Button(window, text="Fetch Data", command=fetch_and_display_data, font=("Arial", 15))
    fetch_data_button.pack(pady=10)

    data_label = tk.Label(window, text="Data will be shown here", font=("Arial", 12))
    data_label.pack(pady=10)

    back_button = tk.Button(window, text="Back to menu", command=start_app, font=("Arial", 15))
    back_button.pack(pady=20)

def base1():
    clear_window()

    for i in range(1, 4):  # Пример для трех классов
        class_button = tk.Button(window, text=f"Class {i}", command=lambda i=i: show_class_data(i), font=("Arial", 15))
        class_button.pack(pady=10)

    back_button = tk.Button(window, text="Back to menu", command=start_app)
    back_button.pack(pady=20)

# Function to start the main application (modified to use the same window)
def start_app():
    clear_window()

    window.title("Analysis Started")

    # Menu -----------------------------
    lbl1 = tk.Label(text="Menu", font=("Arial", 50), fg="black")  # same way bg
    lbl1.place(relx=0.5, rely=0.1, anchor="center")

    Button(window, text="Open base's", command=base1, cursor="hand2", font=("Arial", 30), bg="black",
           fg="white").place(relx=0.6, rely=0.3)

    Button(window, text="Open camera's", command=camera_option, cursor="hand2", font=("Arial", 30), bg="black",
           fg="white").place(relx=0.6, rely=0.6)

    # function defined to exit from window1
    def exit_win1():
        if mbox.askokcancel("Exit", "Do you want to exit?"):
            window.destroy()

    # created exit button
    Button(window, text="EXIT", command=exit_win1, cursor="hand2", font=("Arial", 25), bg="red", fg="black").place(
        relx=0.5, rely=0.85)

# Created a start button
Button(window, text="START",command=start_app,font=("Arial", 25), bg = "green", fg = "black", cursor="hand2", borderwidth=3, relief="raised").place(relx=0.25, rely=0.7, anchor="center")

# Exit button created
Button(window, text="EXIT",command=exit_win,font=("Arial", 25), bg = "red", fg = "black", cursor="hand2", borderwidth=3, relief="raised").place(relx=0.6, rely=0.7, anchor="center")

window.protocol("WM_DELETE_WINDOW", exit_win)
window.mainloop()
