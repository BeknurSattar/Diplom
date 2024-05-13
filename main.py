import datetime
import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
from test import Page  # Импортируй твой основной класс, здесь предполагается, что он находится в файле main.py
from pages.camera_page import CameraPage
from pages.data_page import DataPage

class TestDataPage(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = MagicMock()
        self.app.current_language = 'ru'
        self.data_page = DataPage(self.root, self.app, user_id=123)

    @patch('data_page.connect_db')
    @patch('data_page.messagebox.showerror')
    def test_generate_buttons(self, mock_showerror, mock_connect_db):
        # Настройка моков базы данных
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect_db.return_value = mock_conn
        # Настройка возвращаемых значений курсора
        mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]

        # Настройка возвращаемого значения для position_id
        self.data_page.get_user_position_id = MagicMock(return_value=42)

        # Вызов тестируемой функции
        self.data_page.generate_buttons()

        # Проверка, что запрос к базе данных выполняется с правильными параметрами
        mock_cursor.execute.assert_called_with(
            """
                SELECT DISTINCT o.class_id 
                FROM occupancy o
                JOIN camera_permissions cp ON o.class_id = cp.camera_id
                WHERE cp.position_id = %s
                ORDER BY o.class_id;
            """, (42,))

        # Проверка, что кнопки созданы для каждого class_id
        self.assertEqual(len(self.data_page.buttons), 3)
        # Проверка, что ошибок не было
        mock_showerror.assert_not_called()

        # Завершение и закрытие
        mock_cursor.close.assert_called()
        mock_conn.close.assert_called()

    def tearDown(self):
        self.root.destroy()


if __name__ == '__main__':
    unittest.main()
