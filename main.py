import sys
from PySide6.QtWidgets import QApplication
from app import LanguageLearningApp

def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Установка стиля
    
    window = LanguageLearningApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()