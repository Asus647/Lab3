# Настройки приложения
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent

# Пути к файлам
DATABASE_PATH = BASE_DIR / "data" / "language_app.db"
LOG_FILE = BASE_DIR / "logs" / "app.log"

# Создание директорий
for path in [DATABASE_PATH.parent, LOG_FILE.parent]:
    path.mkdir(parents=True, exist_ok=True)

# Настройки приложения
APP_NAME = "Language Learning App"
APP_VERSION = "1.0.0"
SUPPORTED_LANGUAGES = ["English", "Spanish", "French", "German", "Japanese", "Chinese", "Russian"]
DEFAULT_LANGUAGE = "English"
DIFFICULTY_LEVELS = [str(i) for i in range(1, 6)]  # 1-5