import pytest
from PySide6.QtWidgets import QApplication
from app import LanguageLearningApp
import tempfile
import os

# Создаем QApplication один раз для всех тестов
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

class TestLanguageLearningApp:
    @pytest.fixture
    def app(self, qapp, monkeypatch):
        """Фикстура для создания приложения с временной БД"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Мокаем путь к БД
        import settings
        monkeypatch.setattr(settings, 'DATABASE_PATH', db_path)
        
        app_instance = LanguageLearningApp()
        yield app_instance
        
        # Очистка
        app_instance.db._get_connection().close()
        os.unlink(db_path)
        app_instance.close()
    
    def test_app_creation(self, app):
        """Тест создания приложения"""
        assert app is not None
        assert app.windowTitle().startswith("Language Learning App")
    
    def test_table_exists(self, app):
        """Тест наличия таблицы"""
        assert app.table is not None
        assert app.table.columnCount() == 6
    
    def test_input_fields_exist(self, app):
        """Тест наличия полей ввода"""
        assert app.word_input is not None
        assert app.translation_input is not None
        assert app.language_combo is not None
        assert app.difficulty_combo is not None
    
    def test_buttons_exist(self, app):
        """Тест наличия кнопок"""
        assert app.add_button is not None
        assert app.delete_button is not None
        assert app.learn_button is not None
        assert app.update_graph_button is not None
    
    def test_add_button_text(self, app):
        """Тест текста кнопки добавления"""
        assert app.add_button.text() == "Добавить слово"
    