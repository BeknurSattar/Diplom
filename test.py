import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import numpy as np
import os
import datetime
from main import Page
from detection.persondetection import DetectorAPI
from pages.auth_page import AuthPage
from pages.register import RegisterPage
from pages.home_page import HomePage
from pages.profile_page import ProfilePage
from pages.data_page import DataPage
from pages.camera_page import CameraPage
from pages.settings_page import SettingsPage
from Helps.utils import *
from Helps.translations import translations
class TestPage(unittest.TestCase):
    """
    Тесты для класса Page из main.py.
    Тестирует загрузку сессии из базы данных, переключение полноэкранного режима, смену языка и навигацию между страницами.
    """
    def setUp(self):
        self.app = Page()

    @patch('main.connect_db')  # Обновите путь для мока connect_db
    def test_load_session_from_db(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, True, 'ru')

        result = self.app.load_session_from_db()

        # Проверка результатов
        self.assertTrue(result)
        self.assertEqual(self.app.user_id, 1)
        self.assertTrue(self.app.is_authenticated)
        self.assertEqual(self.app.current_language, 'ru')

    def test_toggle_fullscreen(self):
        # Первоначально режим полного экрана выключен
        self.assertFalse(self.app.full_screen)

        # Переключаем в полноэкранный режим
        self.app.toggle_fullscreen()
        self.assertTrue(self.app.full_screen)
        self.assertTrue(self.app.attributes('-fullscreen'))

        # Переключаем обратно в оконный режим
        self.app.toggle_fullscreen()
        self.assertFalse(self.app.full_screen)
        self.assertFalse(self.app.attributes('-fullscreen'))

    def test_set_language(self):
        # Проверка начального языка
        self.assertEqual(self.app.current_language, 'ru')

        # Смена языка на английский
        self.app.set_language('en')

        # Проверка, что язык изменился
        self.assertEqual(self.app.current_language, 'en')
        self.assertEqual(self.app.home_button.cget('text'), translations['en']['home'])
        self.assertEqual(self.app.profile_button.cget('text'), translations['en']['profile'])
        self.assertEqual(self.app.exit_button.cget('text'), translations['en']['exit'])

    def test_navigation(self):
        # Проверка начального состояния
        self.assertEqual(self.app.selected_index, 0)

        # Переход на страницу DataPage
        self.app.on_navigation_selected(1)
        self.assertEqual(self.app.selected_index, 1)

        # Переход на страницу CameraPage
        self.app.on_navigation_selected(2)
        self.assertEqual(self.app.selected_index, 2)

    def tearDown(self):
        if self.app:
            self.app.update()
            self.app.destroy()

class TestDetectorAPI(unittest.TestCase):
    """
    Тесты для класса DetectorAPI из detection.persondetection.
    Тестирует инициализацию модели и обработку видео кадров.
    """
    def setUp(self):
        # Мокаем модель YOLO
        self.mock_model = MagicMock()
        self.model_path = 'runs/detect/train2/weights/best.pt'

        # Патчим инициализацию модели YOLO, чтобы использовать мок вместо реальной модели
        patcher = patch('detection.persondetection.YOLO', return_value=self.mock_model)
        self.addCleanup(patcher.stop)
        self.mock_yolo = patcher.start()

        # Создаем экземпляр DetectorAPI
        self.detector = DetectorAPI(self.model_path)

    def test_process_frame(self):
        # Создаем моковый результат модели
        mock_results = MagicMock()
        mock_boxes = MagicMock()
        mock_boxes.xyxy.cpu.return_value.numpy.return_value = np.array([[10, 20, 30, 40]])
        mock_boxes.conf.cpu.return_value.numpy.return_value = np.array([0.9])
        mock_boxes.cls.cpu.return_value.numpy.return_value = np.array([0])
        mock_results[0].boxes = mock_boxes

        self.mock_model.return_value = mock_results

        # Создаем моковое изображение
        mock_image = np.zeros((100, 200, 3))

        # Вызов метода processFrame
        boxes_list, scores, classes, num_boxes = self.detector.processFrame(mock_image)

        # Проверка результатов
        self.assertEqual(boxes_list, [(20, 10, 40, 30)])
        self.assertEqual(scores, [0.9])
        self.assertEqual(classes, [0])
        self.assertEqual(num_boxes, 1)

        # Проверка вызовов
        self.mock_model.assert_called_once_with(mock_image)
        mock_boxes.xyxy.cpu.assert_called_once()
        mock_boxes.conf.cpu.assert_called_once()
        mock_boxes.cls.cpu.assert_called_once()

    def tearDown(self):
        # Закрытие ресурсов
        self.detector.close()

class TestAuthPage(unittest.TestCase):
    """
    Тесты для класса AuthPage из pages.auth_page.
    Тестирует успешный и неуспешный логин, переключение видимости пароля и смену языка.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.auth_page = AuthPage(self.root)
        self.auth_page.create_widgets()

    @patch('pages.auth_page.connect_db')
    def test_login_success(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        hashed_password = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        mock_cursor.fetchone.return_value = (1, hashed_password)

        # Устанавливаем значения полей ввода
        self.auth_page.entry_email.insert(0, 'test@example.com')
        self.auth_page.entry_password.insert(0, 'password')

        # Вызов метода login
        self.auth_page.login()

        # Проверка успешной аутентификации
        self.assertTrue(self.auth_page.is_authenticated)
        self.assertEqual(self.auth_page.user_id, 1)

    @patch('pages.auth_page.connect_db')
    def test_login_failure_invalid_password(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        hashed_password = bcrypt.hashpw('wrongpassword'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        mock_cursor.fetchone.return_value = (1, hashed_password)

        # Устанавливаем значения полей ввода
        self.auth_page.entry_email.insert(0, 'test@example.com')
        self.auth_page.entry_password.insert(0, 'password')

        # Вызов метода login
        self.auth_page.login()

        # Проверка, что аутентификация не удалась
        self.assertFalse(self.auth_page.is_authenticated)

    def test_toggle_password_visibility(self):
        # Проверка начального состояния (пароль скрыт)
        self.assertEqual(self.auth_page.entry_password.cget('show'), '*')

        # Переключаем видимость пароля
        self.auth_page.show_password_var.set(True)
        self.auth_page.toggle_password_visibility()

        # Проверка, что пароль отображается
        self.assertEqual(self.auth_page.entry_password.cget('show'), '')

        # Переключаем обратно видимость пароля
        self.auth_page.show_password_var.set(False)
        self.auth_page.toggle_password_visibility()

        # Проверка, что пароль скрыт
        self.assertEqual(self.auth_page.entry_password.cget('show'), '*')

    def test_change_language(self):
        # Проверка начального языка
        self.assertEqual(self.auth_page.current_language, 'ru')

        # Смена языка на английский
        self.auth_page.change_language('English')

        # Проверка, что язык изменился
        self.assertEqual(self.auth_page.current_language, 'en')
        self.assertEqual(self.auth_page.label_email.cget('text'), translations['en']['Email'])

    def tearDown(self):
        self.root.destroy()

class TestRegisterPage(unittest.TestCase):
    """
    Тесты для класса RegisterPage из pages.register.
    Тестирует успешную регистрацию, валидацию пароля и смену языка.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.register_page = RegisterPage(self.root)
        self.register_page.create_widgets()

    @patch('pages.register.connect_db')  # Обновите путь для мока connect_db
    def test_register_success(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (False,)  # Email не существует

        # Устанавливаем значения полей ввода
        self.register_page.entry_username.insert(0, 'testuser')
        self.register_page.entry_email.insert(0, 'test@example.com')
        self.register_page.entry_password.insert(0, 'Password123!')
        self.register_page.entry_confirm_password.insert(0, 'Password123!')

        # Вызов метода register
        with patch('tkinter.messagebox.showinfo') as mock_showinfo:
            self.register_page.register()
            mock_showinfo.assert_called_once_with(translations['ru']['success'], translations['ru']['Registration_completed'])

        # Проверка успешной регистрации
        self.assertTrue(self.register_page.is_valid_email('test@example.com'))
        self.assertTrue(self.register_page.is_unique_email('test@example.com', mock_conn))
        self.assertTrue(self.register_page.validate_password('Password123!')[0])

    def test_validate_password(self):
        # Проверка различных вариантов паролей
        valid_password = 'Password123!'
        short_password = 'Pass12!'
        no_uppercase = 'password123!'
        no_lowercase = 'PASSWORD123!'
        no_digit = 'Password!'
        no_special = 'Password123'

        self.assertTrue(self.register_page.validate_password(valid_password)[0])
        self.assertFalse(self.register_page.validate_password(short_password)[0])
        self.assertFalse(self.register_page.validate_password(no_uppercase)[0])
        self.assertFalse(self.register_page.validate_password(no_lowercase)[0])
        self.assertFalse(self.register_page.validate_password(no_digit)[0])
        self.assertFalse(self.register_page.validate_password(no_special)[0])

    def test_change_language(self):
        # Проверка начального языка
        self.assertEqual(self.register_page.current_language, 'ru')

        # Смена языка на английский
        self.register_page.current_language = 'en'
        self.register_page.update_language()

        # Проверка, что язык изменился
        self.assertEqual(self.register_page.current_language, 'en')
        self.assertEqual(self.register_page.label_email.cget('text'), translations['en']['Email'])

    def tearDown(self):
        self.root.destroy()

class TestHomePage(unittest.TestCase):
    """
    Тесты для класса HomePage из pages.home_page.
    Тестирует отображение последних графиков и их наличие.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.app.current_language = 'ru'
        self.home_page = HomePage(self.root, self.app, user_id=123)

    @patch('pages.home_page.connect_db')  # Обновите путь для мока connect_db
    def test_display_latest_graphs_no_graphs(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        frame = tk.Frame(self.root)
        self.home_page.display_latest_graphs(frame)

        # Проверка наличия сообщения "No graphs found"
        center_frame = frame.winfo_children()[0]
        label = center_frame.winfo_children()[0]
        self.assertEqual(label.cget('text'), translations[self.app.current_language]['no_graphs_found'])

    def tearDown(self):
        if self.root:
            self.root.update()
            self.root.destroy()

class TestProfilePage(unittest.TestCase):
    """
    Тесты для класса ProfilePage из pages.profile_page.
    Тестирует загрузку профиля пользователя и смену пароля.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.profile_page = ProfilePage(self.root, user_id=123)

    @patch('pages.profile_page.connect_db')  # Обновите путь для мока connect_db
    def test_load_user_profile(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ('Test User', 'test@example.com', 'Admin', 'Images/icon.jpg')

        self.profile_page.load_user_profile()

        # Проверка результатов
        self.assertEqual(self.profile_page.username, 'Test User')
        self.assertEqual(self.profile_page.email, 'test@example.com')
        self.assertEqual(self.profile_page.position, 'Admin')
        self.assertEqual(self.profile_page.image_path, 'Images/icon.jpg')

        # Вызовем display_user_info, чтобы обновить метки
        self.profile_page.display_user_info()
        self.profile_page.set_language('ru')  # Устанавливаем язык для отображения

        # Проверка вызова метода отображения информации о пользователе
        expected_username = f"{translations['ru']['username']}: Test User"
        self.assertEqual(self.profile_page.label_username['text'], expected_username)
        expected_email = f"{translations['ru']['email']}: test@example.com"
        self.assertEqual(self.profile_page.label_email['text'], expected_email)
        expected_position = f"{translations['ru']['position']}: Admin"
        self.assertEqual(self.profile_page.label_position['text'], expected_position)

    @patch('pages.profile_page.connect_db')  # Обновите путь для мока connect_db
    @patch('pages.profile_page.simpledialog.askstring')  # Обновите путь для мока simpledialog.askstring
    @patch('pages.profile_page.messagebox.showinfo')  # Обновите путь для мока messagebox.showinfo
    def test_change_password(self, mock_showinfo, mock_askstring, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        new_password = 'NewPassword123!'
        confirm_password = 'NewPassword123!'
        mock_askstring.side_effect = [new_password, confirm_password]

        self.profile_page.change_password()

        # Проверка, что метод execute был вызван
        self.assertTrue(mock_cursor.execute.called)
        args, kwargs = mock_cursor.execute.call_args
        self.assertEqual(args[0], "UPDATE users SET password = %s WHERE user_id = %s")
        self.assertEqual(args[1][1], self.profile_page.user_id)

        # Проверка, что сообщение о успешной смене пароля было показано
        mock_showinfo.assert_called_with(translations[self.profile_page.current_language]['success'], translations[self.profile_page.current_language]['password_successfully_changed'])

    def tearDown(self):
        if self.root:
            self.root.update()
            self.root.destroy()

class TestDataPage(unittest.TestCase):
    """
    Тесты для класса DataPage из pages.data_page.
    Тестирует получение и отображение данных, а также генерацию кнопок для доступных аудиторий.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.app.current_language = 'ru'
        self.data_page = DataPage(self.root, self.app, user_id=15)

    @patch('pages.data_page.connect_db')  # Обновите путь для мока connect_db
    def test_fetch_and_display_data(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [(None,), ('2023-01-01 12:00:00',)]
        mock_cursor.fetchall.return_value = [('2023-01-01 12:00:00', 10), ('2023-01-02 12:00:00', 20)]

        self.data_page.show_class_data(1)

        # Проверка получения данных и обновления текстового виджета
        self.data_page.fetch_and_display_data(1)
        expected_text = f"{translations['ru']['last_10_detections'].format(class_id=1)}\n\n"
        expected_text += f"{translations['ru']['Datae']}: 2023-01-01 12:00:00, {translations['ru']['Caounte']}: 10\n"
        expected_text += f"{translations['ru']['Datae']}: 2023-01-02 12:00:00, {translations['ru']['Caounte']}: 20\n"

        self.assertEqual(self.data_page.data_text.get("1.0", tk.END).strip(), expected_text.strip())

    @patch('pages.data_page.connect_db')  # Обновите путь для мока connect_db
    def test_generate_buttons(self, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]

        self.data_page.generate_buttons()

        # Проверка, что кнопки были созданы и отображены
        self.assertEqual(len(self.data_page.buttons), 3)
        self.assertIn(1, self.data_page.buttons)
        self.assertIn(2, self.data_page.buttons)
        self.assertIn(3, self.data_page.buttons)

    def tearDown(self):
        if self.root:
            self.root.update()
            self.root.destroy()

class TestCameraPage(unittest.TestCase):
    """
    Тесты для класса CameraPage из pages.camera_page.
    Тестирует получение идентификатора должности пользователя, получение доступных видеофайлов и их отображение.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.app.current_language = 'en'  # Устанавливаем значение current_language
        self.camera_page = CameraPage(self.root, self.app, user_id=15)

    @patch('pages.camera_page.connect_db')
    def test_get_user_position_id(self, mock_connect_db):
        # Настройка mock для базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (15,)

        position_id = self.camera_page.get_user_position_id()

        # Проверка, что был выполнен правильный запрос к базе данных
        mock_cursor.execute.assert_called_once_with("SELECT position_id FROM users WHERE user_id = %s;", (15,))
        self.assertEqual(position_id, 15)

    @patch('pages.camera_page.connect_db')
    def test_get_video_files_for_user(self, mock_connect_db):
        # Настройка mock для базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (15,)
        mock_cursor.fetchall.return_value = [(1, 'video1.mp4'), (2, 'video2.mp4')]

        video_files = self.camera_page.get_video_files_for_user()

        # Проверка, что были выполнены правильные запросы к базе данных
        self.assertEqual(mock_cursor.execute.call_count, 2)
        mock_cursor.execute.assert_any_call("SELECT position_id FROM users WHERE user_id = %s;", (15,))
        mock_cursor.execute.assert_any_call("""
                SELECT c.id, c.path
                FROM cameras c
                JOIN camera_permissions cp ON c.id = cp.camera_id
                WHERE cp.position_id = %s;
                """, (15,))
        self.assertEqual(video_files, {1: 'video1.mp4', 2: 'video2.mp4'})

    def tearDown(self):
        self.root.destroy()
class TestSettingsPage(unittest.TestCase):
    """
    Тесты для класса SettingsPage из pages.settings_page.
    Тестирует открытие справочного документа, смену языка и безопасный выход.
    """
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.app.current_language = 'ru'
        self.settings_page = SettingsPage(self.root, self.app, user_id=123)

    @patch('pages.settings_page.webbrowser.open')
    @patch('pages.settings_page.os.path.exists')
    def test_open_help_document(self, mock_exists, mock_open):
        # Настройка моков
        mock_exists.return_value = True

        # Вызов тестируемого метода
        self.settings_page.open_help_document()

        # Проверка вызовов
        help_path = os.path.join('Helps', 'Diplom.pdf')
        mock_exists.assert_called_once_with(help_path)
        mock_open.assert_called_once_with(help_path)

    @patch('pages.settings_page.webbrowser.open')
    @patch('pages.settings_page.os.path.exists')
    def test_open_help_document_file_not_found(self, mock_exists, mock_open):
        # Настройка моков
        mock_exists.return_value = False

        with patch('tkinter.messagebox.showerror') as mock_showerror:
            self.settings_page.open_help_document()
            # Проверка вызовов
            help_path = os.path.join('Helps', 'Diplom.pdf')
            mock_exists.assert_called_once_with(help_path)
            mock_open.assert_not_called()
            mock_showerror.assert_called_once()

    def test_set_language(self):
        new_language = 'en'
        self.settings_page.set_language(new_language)
        self.assertEqual(self.settings_page.current_language, new_language)
        self.assertEqual(self.settings_page.theme_button.cget('text'), translations[new_language]['change_theme'])
        self.assertEqual(self.settings_page.help_button.cget('text'), translations[new_language]['help'])
        self.assertEqual(self.settings_page.language_label.cget('text'), translations[new_language]['select_language'])
        self.assertEqual(self.settings_page.exit_button.cget('text'), translations[new_language]['exit'])

    @patch('tkinter.messagebox.askokcancel', return_value=True)
    def test_safe_exit(self, mock_askokcancel):
        # Вызов тестируемого метода
        self.settings_page.safe_exit()

        # Проверка вызовов
        mock_askokcancel.assert_called_once_with(
            translations[self.settings_page.current_language]['exit_confirmation_title'],
            translations[self.settings_page.current_language]['confirm_exit']
        )
        self.app.logout.assert_called_once()

    def tearDown(self):
        self.root.destroy()

class TestUtils(unittest.TestCase):
    """
    Тесты для утилитных функций из Helps.utils.
    Тестирует подключение к базе данных, вставку данных, хеширование и проверку пароля.
    """
    @patch('psycopg2.connect')
    def test_connect_db_success(self, mock_connect):
        mock_connect.return_value = MagicMock()
        conn = connect_db()
        self.assertIsNotNone(conn)
        mock_connect.assert_called_once()

    @patch('psycopg2.connect')
    def test_connect_db_failure(self, mock_connect):
        mock_connect.side_effect = psycopg2.OperationalError
        conn = connect_db()
        self.assertIsNone(conn)
        mock_connect.assert_called_once()

    @patch('Helps.utils.connect_db')
    @patch('Helps.utils.datetime')
    def test_insert_data_success(self, mock_datetime, mock_connect_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)

        insert_data(10, 1, 1, datetime(2024, 1, 1, 0, 0, 0))

        mock_connect_db.assert_called_once()
        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO occupancy (detection_date, people_count, class_id, user_id, session_start) VALUES (%s, %s, %s, %s, %s)",
            (datetime(2024, 1, 1, 0, 0, 0), 10, 1, 1, datetime(2024, 1, 1, 0, 0, 0))
        )
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('Helps.utils.connect_db')
    @patch('Helps.utils.datetime')
    def test_insert_data_failure(self, mock_datetime, mock_connect_db):
        mock_connect_db.return_value = None
        mock_datetime.now.return_value = datetime(2024, 1, 1, 0, 0, 0)

        with self.assertRaises(Exception):
            insert_data(10, 1, 1, datetime(2024, 1, 1, 0, 0, 0))

        mock_connect_db.assert_called_once()

    def test_hash_password(self):
        password = 'password123'
        hashed = hash_password(password)
        self.assertTrue(bcrypt.checkpw(password.encode(), hashed))

    def test_check_password(self):
        password = 'password123'
        hashed = hash_password(password)
        self.assertTrue(check_password(hashed, password))
        self.assertFalse(check_password(hashed, 'wrongpassword'))


if __name__ == '__main__':
    unittest.main()