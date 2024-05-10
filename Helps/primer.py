def show_video_in_box(self, index, box, dlg_modal):
    if 0 <= index < len(self.videos):
        video_source = self.videos[index]
        cap = cv2.VideoCapture(video_source)
        dlg_modal.destroy()

        # Удаляем предыдущую видео метку из бокса
        for widget in box.winfo_children():
            widget.destroy()

        box_width = box.winfo_width()
        box_height = box.winfo_height()

        ret, frame = cap.read()
        if ret:
            frame_height, frame_width, _ = frame.shape
            aspect_ratio = frame_width / frame_height
            video_width, video_height = self.calculate_video_dimensions(aspect_ratio, box_width, box_height)

            imgtk = self.create_video_image(frame, video_width, video_height)
            video_label = tk.Label(box, width=video_width, height=video_height, image=imgtk)
            video_label.imgtk = imgtk
            video_label.pack(fill="both", expand=True)

            remove_button = tk.Button(box, text="Убрать видео",
                                      command=lambda: self.remove_video(video_label, cap, box))
            remove_button.pack(side="left", padx=5)

            save_button = tk.Button(box, text="Сохранить в базу", command=lambda: None)
            save_button.pack(side="left", padx=5)

            self.update_image(cap, video_label, video_width, video_height, index)


def calculate_video_dimensions(self, aspect_ratio, box_width, box_height):
    if aspect_ratio * box_height > box_width:
        video_height = box_height
        video_width = int(video_height * aspect_ratio)
    else:
        video_width = box_width
        video_height = int(video_width / aspect_ratio)
    return video_width, video_height


def create_video_image(self, frame, video_width, video_height):
    frame_resized = cv2.resize(frame, (video_width, video_height))
    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    return ImageTk.PhotoImage(image=img)


def update_image(self, cap, video_label, video_width, video_height, index):
    global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
    max_count3 = 0
    framex3 = []
    county3 = []
    max3 = []
    avg_acc3_list = []
    max_avg_acc3_list = []
    max_acc3 = 0
    max_avg_acc3 = 0

    odapi = DetectorAPI()
    threshold = 0.7

    x3 = 0

    people_data = []  # Список для хранения данных о количестве людей по времени
    accuracy_data = []  # Список для хранения данных о точности определения по времени

    def analyze_and_update():
        global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3, x3
        x3 = 0
        ret, frame = cap.read()
        if ret:
            imgtk = self.create_video_image(frame, video_width, video_height)
            video_label.configure(image=imgtk)
            video_label.imgtk = imgtk

            # Анализируем изображение на наличие людей
            img_resized = cv2.resize(frame, (video_width, video_height))  # Подгоняем размер кадра под детектор
            boxes, scores, classes, num = odapi.processFrame(img_resized)
            person = 0
            acc = 0
            for i in range(len(boxes)):
                if classes[i] == 1 and scores[i] > threshold:
                    box = boxes[i]
                    person += 1
                    cv2.rectangle(img_resized, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)  # cv2.FILLED
                    cv2.putText(img_resized, f'P{person, round(scores[i], 2)}', (box[1] - 30, box[0] - 8),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)  # (75,0,130),
                    acc += scores[i]
                    if (scores[i] > max_acc3):
                        max_acc3 = scores[i]
            if (person > max_count3):
                max_count3 = person

            county3.append(person)
            x3 += 1
            framex3.append(x3)
            if (person >= 1):
                avg_acc3_list.append(acc / person)
                if ((acc / person) > max_avg_acc3):
                    max_avg_acc3 = (acc / person)
            else:
                avg_acc3_list.append(acc)

            start_periodic_data_insert(person, index)

            for i in range(len(framex3)):
                max3.append(max_count3)
                max_avg_acc3_list.append(max_avg_acc3)

                # Сохраняем данные о количестве людей и точности определения по времени
            people_data.append(person)
            accuracy_data.append(acc / person if person > 0 else 0)

            # Повторяем анализ и обновление изображения через 10 миллисекунд
            video_label.after(10, analyze_and_update)
        else:
            # Создаем графики и сохраняем их
            create_and_save_graphs(people_data, accuracy_data, index)

    def create_and_save_graphs(people_data, accuracy_data, class_id):
        try:
            # Создаем график количества людей по времени
            plt.plot(framex3, people_data)
            plt.xlabel('Время')
            plt.ylabel('Количество людей')
            plt.title('График количества людей по времени')
            people_graph_buf = io.BytesIO()
            plt.savefig(people_graph_buf, format='png')
            people_graph_buf.seek(0)
            people_graph_data = people_graph_buf.read()  # Читаем содержимое буфера

            plt.close()

            # Создаем график точности определения по времени
            plt.plot(framex3, accuracy_data)
            plt.xlabel('Время')
            plt.ylabel('Точность определения')
            plt.title('График точности определения по времени')
            accuracy_graph_buf = io.BytesIO()
            plt.savefig(accuracy_graph_buf, format='png')
            accuracy_graph_buf.seek(0)
            accuracy_graph_data = accuracy_graph_buf.read()  # Читаем содержимое буфера

            plt.close()

            conn = connect_db()
            # Сохраняем графики в базу данных
            cur = conn.cursor()

            # Преобразуем данные графиков в бинарные данные
            cur.execute("INSERT INTO graphs (class_id, graph_name, graph_data) VALUES (%s, %s, %s);",
                        (class_id, 'people_graph', psycopg2.Binary(people_graph_data)))
            cur.execute("INSERT INTO graphs (class_id, graph_name, graph_data) VALUES (%s, %s, %s);",
                        (class_id, 'accuracy_graph', psycopg2.Binary(accuracy_graph_data)))
            conn.commit()
            cur.close()

            print("Графики успешно сохранены в базу данных.")
        except psycopg2.Error as e:
            print("Ошибка сохранения графиков в базу данных: ", e)

    # Запускаем анализ и обновление изображения в отдельном потоке
    threading.Thread(target=analyze_and_update).start()


def remove_video(self, video_label, cap, box):
    cap.release()
    stop_periodic_data_insert()
    video_label.destroy()
    for widget in box.winfo_children():
        widget.destroy()
    self.create_initial_box_view(box)

layer_outputs = net.getUnconnectedOutLayers()
if isinstance(layer_outputs[0], np.ndarray):
    # Для версий OpenCV, возвращающих массив массивов
    output_layers = [layer_names[i[0] - 1] for i in layer_outputs]
else:
    # Для версий OpenCV, возвращающих массив индексов
    output_layers = [layer_names[i - 1] for i in layer_outputs]



    def show_class_data(self, class_id):
        """Отображение данных класса или графиков."""
        self.content.destroy()
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")

        """Получение контента страницы."""
        self.data_text = scrolledtext.ScrolledText(self.content, wrap=tk.WORD, width=50, height=10)
        self.data_text.pack(pady=10)

        # Добавление кнопок для загрузки графиков и данных
        button_frame = tk.Frame(self.content)
        button_frame.pack(pady=10)

        data_button = tk.Button(button_frame, text="Показать данные",
                                command=lambda: self.fetch_and_display_data(1))  # Пример class_id=1
        data_button.pack(side="left", padx=5)

        graph1_button = tk.Button(button_frame, text="График 1", command=lambda: self.display_graph(class_id, 1))
        graph1_button.pack(side="left", padx=5)

        graph2_button = tk.Button(button_frame, text="График 2", command=lambda: self.display_graph(class_id, 2))
        graph2_button.pack(side="left", padx=5)

        back_button = tk.Button(self.content, text="Back to menu", command=self.back_to_menu)
        back_button.pack(pady=10)


    def back_to_menu(self):
        """Возвращение в меню."""
        self.content.destroy()
        self.content = tk.Frame(self)
        self.content.pack(expand=True, fill="both")
        self.get_content()

    def load_graph_from_db(self, class_id, base_graph_name):
        try:
            conn = connect_db()
            cur = conn.cursor()
            # Запрос последнего графика по class_id и базовому имени графика
            cur.execute("""
                SELECT graph_path FROM graphs
                WHERE class_id = %s AND graph_name LIKE %s
                ORDER BY upload_date DESC, id DESC
                LIMIT 1;
            """, (class_id, f'{base_graph_name}_{class_id}%'))
            graph_path = cur.fetchone()
            if graph_path:
                img = Image.open(graph_path[0])
                return img
            cur.close()
        except psycopg2.Error as e:
            print(f"Ошибка выполнения запроса к базе данных: {e}")
        return None


    def display_graph(self, class_id, graph_type):
        """Отображение выбранного графика."""
        # Формирование базового имени графика
        base_graph_name = 'people_graph' if graph_type == 1 else 'accuracy_graph'
        # Запрос для получения самого последнего графика для данного класса
        graph_name = f"{base_graph_name}_{class_id}"
        img = self.load_graph_from_db(class_id, graph_name)
        if img:
            img = img.resize((500, 400), Image.LANCZOS)
            imgtk = ImageTk.PhotoImage(image=img)
            if hasattr(self, 'graph_label'):
                self.graph_label.config(image=imgtk)
                self.graph_label.image = imgtk
            else:
                self.graph_label = tk.Label(self.content, image=imgtk)
                self.graph_label.image = imgtk
                self.graph_label.pack(pady=10)
        else:
            print("График не найден или ошибка загрузки.")