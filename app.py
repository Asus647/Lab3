import sys
import logging
from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QLineEdit, QComboBox,
    QPushButton, QMenuBar, QMenu, QMessageBox, QSplitter, QTextEdit,
    QFormLayout, QGroupBox, QStatusBar, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models import Word, UserProgress
from database import DatabaseManager
from exceptions import EmptyFieldError, InvalidDifficultyError, DatabaseError
import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MplCanvas(FigureCanvas):
    """Холст для matplotlib"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.axes.set_facecolor('#f0f0f0')
        self.fig.patch.set_facecolor('#ffffff')


class LanguageLearningApp(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.current_word_id: Optional[int] = None
        
        self._setup_ui()
        self._setup_menu()
        self._load_data()
        self._setup_connections()
        
        logger.info("Приложение запущено")
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        self.setWindowTitle(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout(central_widget)
        
        # Сплиттер для разделения интерфейса
        splitter = QSplitter(Qt.Vertical)
        
        # Верхняя часть: форма ввода и таблица
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        
        # Форма ввода
        input_group = QGroupBox("Добавить новое слово")
        input_layout = QFormLayout()
        
        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Введите слово на иностранном языке")
        
        self.translation_input = QLineEdit()
        self.translation_input.setPlaceholderText("Введите перевод")
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(settings.SUPPORTED_LANGUAGES)
        self.language_combo.setCurrentText(settings.DEFAULT_LANGUAGE)
        
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(settings.DIFFICULTY_LEVELS)
        self.difficulty_combo.setCurrentText("2")
        
        input_layout.addRow("Слово:", self.word_input)
        input_layout.addRow("Перевод:", self.translation_input)
        input_layout.addRow("Язык:", self.language_combo)
        input_layout.addRow("Сложность:", self.difficulty_combo)
        
        input_group.setLayout(input_layout)
        top_layout.addWidget(input_group)
        
        # Кнопки действий
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Добавить слово")
        self.add_button.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.delete_button = QPushButton("Удалить выбранное")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        self.delete_button.setEnabled(False)
        
        self.learn_button = QPushButton("Отметить как изученное")
        self.learn_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.learn_button.setEnabled(False)
        
        self.update_graph_button = QPushButton("Обновить график")
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.learn_button)
        button_layout.addWidget(self.update_graph_button)
        button_layout.addStretch()
        
        top_layout.addLayout(button_layout)
        
        # Таблица слов
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Слово", "Перевод", "Язык", "Сложность", "Последний повтор"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        
        top_layout.addWidget(QLabel("Ваши слова:"))
        top_layout.addWidget(self.table)
        
        splitter.addWidget(top_widget)
        
        # Нижняя часть: график и логи
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        # График
        graph_widget = QWidget()
        graph_layout = QVBoxLayout(graph_widget)
        
        self.graph_label = QLabel("Прогресс изучения (последние 7 дней)")
        self.graph_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.canvas = MplCanvas(self, width=6, height=4, dpi=100)
        
        graph_layout.addWidget(self.graph_label)
        graph_layout.addWidget(self.canvas)
        
        # Статистика
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        self.stats_label = QLabel("Ваша статистика:")
        self.stats_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.total_words_label = QLabel("Всего слов: 0")
        self.learned_words_label = QLabel("Изучено слов: 0")
        self.progress_label = QLabel("Прогресс: 0%")
        self.streak_label = QLabel("Серия дней: 0")
        
        stats_layout.addWidget(self.stats_label)
        stats_layout.addWidget(self.total_words_label)
        stats_layout.addWidget(self.learned_words_label)
        stats_layout.addWidget(self.progress_label)
        stats_layout.addWidget(self.streak_label)
        stats_layout.addStretch()
        
        # Логи
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        
        log_label = QLabel("Лог действий:")
        log_label.setFont(QFont("Arial", 10, QFont.Bold))
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_text)
        
        bottom_layout.addWidget(graph_widget, 2)
        bottom_layout.addWidget(stats_widget, 1)
        bottom_layout.addWidget(log_widget, 1)
        
        splitter.addWidget(bottom_widget)
        splitter.setSizes([500, 300])
        
        main_layout.addWidget(splitter)
        
        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")
    
    def _setup_menu(self):
        """Настройка меню"""
        menubar = self.menuBar()
        
        # Меню
        file_menu = menubar.addMenu("Меню")
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_connections(self):
        """Настройка сигналов"""
        self.add_button.clicked.connect(self._add_word)
        self.delete_button.clicked.connect(self._delete_word)
        self.learn_button.clicked.connect(self._mark_as_learned)
        self.update_graph_button.clicked.connect(self._update_graph)
        self.table.itemSelectionChanged.connect(self._on_table_selection)
    
    def _load_data(self):
        """Загрузка данных из БД"""
        try:
            # Загрузка слов
            words = self.db.get_all_words()
            self._populate_table(words)
            
            # Загрузка статистики
            self._update_stats()
            
            # Обновление графика
            self._update_graph()
            
            self.status_bar.showMessage(f"Загружено {len(words)} слов")
            self._log_action(f"Загружено {len(words)} слов из базы данных")
            
        except Exception as e:
            self._show_error(f"Ошибка загрузки данных: {str(e)}")
            logger.error(f"Ошибка загрузки данных: {e}")
    
    def _populate_table(self, words):
        """Заполнение таблицы словами"""
        self.table.setRowCount(len(words))
        
        for row, word in enumerate(words):
            self.table.setItem(row, 0, QTableWidgetItem(str(word.id or "")))
            self.table.setItem(row, 1, QTableWidgetItem(word.word))
            self.table.setItem(row, 2, QTableWidgetItem(word.translation))
            self.table.setItem(row, 3, QTableWidgetItem(word.language))
            self.table.setItem(row, 4, QTableWidgetItem(str(word.difficulty)))
            self.table.setItem(row, 5, QTableWidgetItem(
                word.last_reviewed.strftime("%Y-%m-%d %H:%M") 
                if word.last_reviewed else "Не изучено"
            ))
    
    def _update_stats(self):
        """Обновление статистики"""
        try:
            progress = self.db.get_user_progress()
            
            self.total_words_label.setText(f"Всего слов: {progress.total_words}")
            self.learned_words_label.setText(f"Изучено слов: {progress.learned_words}")
            self.progress_label.setText(
                f"Прогресс: {progress.get_progress_percentage():.1f}%"
            )
            self.streak_label.setText(f"Серия дней: {progress.streak_days}")
            
        except Exception as e:
            logger.error(f"Ошибка обновления статистики: {e}")
    
    def _update_graph(self):
        """Обновление графика прогресса"""
        try:
            stats = self.db.get_daily_stats(days=7)
            
            if not stats:
                self.canvas.axes.clear()
                self.canvas.axes.text(0.5, 0.5, 'Нет данных', 
                                     ha='center', va='center',
                                     transform=self.canvas.axes.transAxes)
                self.canvas.draw()
                return
            
            dates = [stat['date'] for stat in stats]
            added = [stat['added'] for stat in stats]
            learned = [stat['learned'] for stat in stats]
            
            self.canvas.axes.clear()
            
            x = range(len(dates))
            width = 0.35
            
            self.canvas.axes.bar([i - width/2 for i in x], added, width, 
                                label='Добавлено', color='#2196F3')
            self.canvas.axes.bar([i + width/2 for i in x], learned, width, 
                                label='Изучено', color='#4CAF50')
            
            self.canvas.axes.set_xlabel('Дата')
            self.canvas.axes.set_ylabel('Количество слов')
            self.canvas.axes.set_title('Статистика за последние 7 дней')
            self.canvas.axes.set_xticks(x)
            self.canvas.axes.set_xticklabels([d.split('-')[-1] + '/' + d.split('-')[-2] 
                                            for d in dates], rotation=45)
            self.canvas.axes.legend()
            self.canvas.axes.grid(True, alpha=0.3)
            
            self.canvas.fig.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"Ошибка обновления графика: {e}")
            self._show_error(f"Ошибка построения графика: {str(e)}")
    
    def _add_word(self):
        """Добавление нового слова"""
        try:
            # Валидация полей
            word = self.word_input.text().strip()
            translation = self.translation_input.text().strip()
            
            if not word:
                raise EmptyFieldError("Слово")
            if not translation:
                raise EmptyFieldError("Перевод")
            
            difficulty = int(self.difficulty_combo.currentText())
            if not 1 <= difficulty <= 5:
                raise InvalidDifficultyError(difficulty)
            
            # Создание объекта слова
            new_word = Word(
                word=word,
                translation=translation,
                language=self.language_combo.currentText(),
                difficulty=difficulty
            )
            
            # Сохранение в БД
            word_id = self.db.add_word(new_word)
            
            # Обновление интерфейса
            self._load_data()
            
            # Очистка полей ввода
            self.word_input.clear()
            self.translation_input.clear()
            
            self.status_bar.showMessage(f"Слово '{word}' добавлено")
            self._log_action(f"Добавлено слово: '{word}' - '{translation}'")
            
            QMessageBox.information(self, "Успех", 
                                  f"Слово '{word}' успешно добавлено!")
            
        except EmptyFieldError as e:
            self._show_error(str(e))
        except InvalidDifficultyError as e:
            self._show_error(str(e))
        except DatabaseError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"Неизвестная ошибка: {str(e)}")
            logger.error(f"Ошибка добавления слова: {e}")
    
    def _delete_word(self):
        """Удаление выбранного слова"""
        if self.current_word_id is None:
            return
        
        try:
            # Получение слова для подтверждения
            words = self.db.get_all_words()
            word_to_delete = None
            for word in words:
                if word.id == self.current_word_id:
                    word_to_delete = word
                    break
            
            if not word_to_delete:
                raise DatabaseError("Слово не найдено")
            
            # Подтверждение удаления
            reply = QMessageBox.question(
                self, 'Подтверждение',
                f"Вы уверены, что хотите удалить слово '{word_to_delete.word}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.db.delete_word(self.current_word_id)
                self._load_data()
                
                self.status_bar.showMessage(f"Слово '{word_to_delete.word}' удалено")
                self._log_action(f"Удалено слово: '{word_to_delete.word}'")
                
        except Exception as e:
            self._show_error(f"Ошибка удаления: {str(e)}")
            logger.error(f"Ошибка удаления слова: {e}")
    
    def _mark_as_learned(self):
        """Отметить слово как изученное"""
        if self.current_word_id is None:
            return
        
        try:
            self.db.mark_as_learned(self.current_word_id)
            self._load_data()
            
            self.status_bar.showMessage("Слово отмечено как изученное")
            self._log_action(f"Слово отмечено как изученное (ID: {self.current_word_id})")
            
            QMessageBox.information(self, "Успех", "Слово отмечено как изученное!")
            
        except Exception as e:
            self._show_error(f"Ошибка: {str(e)}")
            logger.error(f"Ошибка отметки как изученное: {e}")
    
    def _on_table_selection(self):
        """Обработка выбора строки в таблице"""
        selected_items = self.table.selectedItems()
        
        if selected_items:
            row = selected_items[0].row()
            word_id_item = self.table.item(row, 0)
            
            if word_id_item and word_id_item.text():
                self.current_word_id = int(word_id_item.text())
                self.delete_button.setEnabled(True)
                self.learn_button.setEnabled(True)
            else:
                self.current_word_id = None
                self.delete_button.setEnabled(False)
                self.learn_button.setEnabled(False)
        else:
            self.current_word_id = None
            self.delete_button.setEnabled(False)
            self.learn_button.setEnabled(False)
    
    def _export_words(self):
        """Экспорт слов в файл"""
        try:
            words = self.db.get_all_words()
            
            if not words:
                QMessageBox.warning(self, "Экспорт", "Нет слов для экспорта")
                return
            
            # В реальном приложении здесь была бы логика выбора файла
            # и сохранения в CSV/JSON формате
            word_count = len(words)
            
            self._log_action(f"Экспортировано {word_count} слов")
            QMessageBox.information(self, "Экспорт", 
                                  f"Готово к экспорту {word_count} слов\n"
                                  f"(В реальном приложении откроется диалог сохранения)")
            
        except Exception as e:
            self._show_error(f"Ошибка экспорта: {str(e)}")
            logger.error(f"Ошибка экспорта: {e}")
    
    def _show_about(self):
        """Показать информацию о программе"""
        about_text = f"""
        <h2>{settings.APP_NAME}</h2>
        <p>Версия: {settings.APP_VERSION}</p>
        <p>Приложение для изучения иностранных языков</p>
        <p>Функции:</p>
        <ul>
            <li>Добавление и удаление слов</li>
            <li>Отслеживание прогресса</li>
            <li>Визуализация статистики</li>
            <li>Логирование действий</li>
        </ul>
        <p>Поддерживаемые языки: {', '.join(settings.SUPPORTED_LANGUAGES)}</p>
        """
        
        QMessageBox.about(self, "О программе", about_text)
        self._log_action("Открыто окно 'О программе'")
    
    def _log_action(self, message: str):
        """Логирование действия"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        # Добавление в текстовое поле логов
        self.log_text.append(log_message)
        
        # Прокрутка вниз
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
        # Запись в файл логов
        logger.info(message)
    
    def _show_error(self, message: str):
        """Показать сообщение об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)
        logger.error(message)
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        logger.info("Приложение завершает работу")
        event.accept()