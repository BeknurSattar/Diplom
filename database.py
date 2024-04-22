from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
import threading
import cv2
from persondetection import DetectorAPI
import matplotlib.pyplot as plt
from fpdf import FPDF
import psycopg2
from datetime import datetime

Window.clearcolor = (1, 0, 0, 1) 

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


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Создаем стильный заголовок
        title_label = Label(text='Analysis of class',
                            size_hint=(1, None),
                            height=50,
                            font_size='24sp',
                            color=(0, 0, 0, 1))
        layout.add_widget(title_label)
        
        # Добавляем ниже текст с объяснениями
        explanation_text = "Здесь может быть ваш текст с объяснениями о том, как работает ваше приложение, его функции и как его использовать."
        explanation_label = Label(text=explanation_text,
                                  size_hint=(1, None),
                                  font_size='18sp',
                                  color=(0.5, 0.5, 0.5, 1))
        layout.add_widget(explanation_label)
        
        self.add_widget(layout)

class CameraScreen(Screen):
    def camera_option():
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
                data_insert_timer.start()
                data_insert_timer = threading.Timer(30, periodic_data_insert, args=(person, class_id))
                



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

class ClassScreen(Screen):
    pass

class SettingsScreen(Screen):
    pass

class IconicToggleButton(ToggleButton):
    def __init__(self, icon, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = icon
        self.background_down = icon
        # Убрать текст с кнопки
        self.text = ''
        # Установить размер кнопки
        self.size_hint = (None, None)
        self.size = (50, 50)  # Размер кнопки

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'

        self.top_bar = BoxLayout(size_hint_y=None, height=50, size_hint_x=None, width=Window.width, padding=5)
        # Создаем кнопку меню и размещаем ее в левом углу
        self.nav_button = IconicToggleButton(icon='Images/eyeee.png', size_hint=(None, None), size=(50, 50))
        self.nav_button.bind(on_press=self.toggle_nav)
        self.top_bar.add_widget(self.nav_button)

        # Настраиваем отступы в навигационной панели
        self.navigation_panel = BoxLayout(orientation='vertical', size_hint_x=None, width=60, padding=5, spacing=10)
        self.navigation_panel.canvas.before.clear()
        with self.navigation_panel.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.navigation_panel.size, pos=self.navigation_panel.pos)

        self.navigation_panel.bind(pos=self.update_rect, size=self.update_rect)
        
        self.screen_manager = ScreenManager()
        self.screen_manager.add_widget(HomeScreen(name='home'))
        self.screen_manager.add_widget(CameraScreen(name='camera'))
        self.screen_manager.add_widget(ClassScreen(name='class'))
        self.screen_manager.add_widget(SettingsScreen(name='settings'))

        self.content = BoxLayout(orientation='horizontal')
        self.content.add_widget(self.navigation_panel)
        self.content.add_widget(self.screen_manager)
        self.add_widget(self.top_bar)
        self.add_widget(self.content)

        self.navigation_panel.add_widget(IconicButton(icon='Images/home.png', on_press=lambda x: self.switch_screen('home')))
        self.navigation_panel.add_widget(IconicButton(icon='Images/camera.png', on_press=lambda x: self.switch_screen('camera')))
        self.navigation_panel.add_widget(IconicButton(icon='Images/book-alt.png', on_press=lambda x: self.switch_screen('class')))
        self.navigation_panel.add_widget(IconicButton(icon='Images/settings.png', on_press=lambda x: self.switch_screen('settings')))
        self.navigation_panel.add_widget(IconicButton(icon='Images/exit.png', on_press=lambda x: self.exit_app()))

    def update_rect(self, *args):
        self.rect.pos = self.navigation_panel.pos
        self.rect.size = self.navigation_panel.size

    def switch_screen(self, screen_name):
        self.screen_manager.current = screen_name

    def toggle_nav(self, instance):
        # Анимация для скрытия или показа навигационной панели
        if instance.state == 'normal':
            anim = Animation(width=0, d=0.3)
        else:
            anim = Animation(width=60, d=0.3)
        anim.start(self.navigation_panel)

    def exit_app(self):
        App.get_running_app().stop()

class MainApp(App):
    def build(self):
        self.title = 'Analysis of class occupancy using computer vision methods'
        self.icon = 'Images/eye.ico'  # Убедитесь, что файл иконки находится в той же директории, что и скрипт
        
        return MainLayout()

if __name__ == '__main__':
    MainApp().run() 
