#!/usr/bin/env python3
"""
Скрипт для заполнения базы данных начальными данными
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем родительскую директорию в путь для импорта
sys.path.append(str(Path(__file__).parent))

from models import Word
from database import DatabaseManager
import settings

def seed_database():
    """Заполнение базы данных тестовыми данными"""
    print("🌱 Заполнение базы данных начальными данными...")
    
    db = DatabaseManager()
    
    # Очищаем существующие данные (опционально)
    print("🗑️  Очистка старых данных...")
    with db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM words")
        cursor.execute("UPDATE user_progress SET total_words = 0, learned_words = 0, streak_days = 0")
    
    # Примеры слов для изучения по разным языкам
    words_data = [
        # Английский язык (English)
        {"word": "hello", "translation": "привет", "language": "English", "difficulty": 1},
        {"word": "goodbye", "translation": "до свидания", "language": "English", "difficulty": 1},
        {"word": "thank you", "translation": "спасибо", "language": "English", "difficulty": 1},
        {"word": "please", "translation": "пожалуйста", "language": "English", "difficulty": 2},
        {"word": "beautiful", "translation": "красивый", "language": "English", "difficulty": 2},
        {"word": "difficult", "translation": "сложный", "language": "English", "difficulty": 3},
        {"word": "opportunity", "translation": "возможность", "language": "English", "difficulty": 4},
        {"word": "accomplishment", "translation": "достижение", "language": "English", "difficulty": 5},
        
        # Испанский язык (Spanish)
        {"word": "hola", "translation": "привет", "language": "Spanish", "difficulty": 1},
        {"word": "adiós", "translation": "до свидания", "language": "Spanish", "difficulty": 1},
        {"word": "gracias", "translation": "спасибо", "language": "Spanish", "difficulty": 1},
        {"word": "por favor", "translation": "пожалуйста", "language": "Spanish", "difficulty": 2},
        {"word": "hermoso", "translation": "красивый", "language": "Spanish", "difficulty": 2},
        {"word": "amigo", "translation": "друг", "language": "Spanish", "difficulty": 2},
        {"word": "biblioteca", "translation": "библиотека", "language": "Spanish", "difficulty": 3},
        {"word": "desarrollador", "translation": "разработчик", "language": "Spanish", "difficulty": 4},
        
        # Французский язык (French)
        {"word": "bonjour", "translation": "добрый день", "language": "French", "difficulty": 1},
        {"word": "merci", "translation": "спасибо", "language": "French", "difficulty": 1},
        {"word": "au revoir", "translation": "до свидания", "language": "French", "difficulty": 1},
        {"word": "s'il vous plaît", "translation": "пожалуйста", "language": "French", "difficulty": 2},
        {"word": "amour", "translation": "любовь", "language": "French", "difficulty": 2},
        {"word": "ordinateur", "translation": "компьютер", "language": "French", "difficulty": 3},
        {"word": "restaurant", "translation": "ресторан", "language": "French", "difficulty": 2},
        {"word": "philosophie", "translation": "философия", "language": "French", "difficulty": 5},
        
        # Немецкий язык (German)
        {"word": "hallo", "translation": "привет", "language": "German", "difficulty": 1},
        {"word": "danke", "translation": "спасибо", "language": "German", "difficulty": 1},
        {"word": "bitte", "translation": "пожалуйста", "language": "German", "difficulty": 2},
        {"word": "tschüss", "translation": "пока", "language": "German", "difficulty": 2},
        {"word": "schön", "translation": "красивый", "language": "German", "difficulty": 2},
        {"word": "entschuldigung", "translation": "извините", "language": "German", "difficulty": 4},
        {"word": "freundschaft", "translation": "дружба", "language": "German", "difficulty": 3},
        
        # Японский язык (Japanese)
        {"word": "こんにちは", "translation": "здравствуйте", "language": "Japanese", "difficulty": 2},
        {"word": "ありがとう", "translation": "спасибо", "language": "Japanese", "difficulty": 2},
        {"word": "さようなら", "translation": "до свидания", "language": "Japanese", "difficulty": 3},
        {"word": "お願いします", "translation": "пожалуйста", "language": "Japanese", "difficulty": 4},
        {"word": "愛", "translation": "любовь", "language": "Japanese", "difficulty": 3},
        {"word": "元気", "translation": "энергичный", "language": "Japanese", "difficulty": 4},
        
        # Китайский язык (Chinese)
        {"word": "你好", "translation": "привет", "language": "Chinese", "difficulty": 2},
        {"word": "谢谢", "translation": "спасибо", "language": "Chinese", "difficulty": 2},
        {"word": "再见", "translation": "до свидания", "language": "Chinese", "difficulty": 2},
        {"word": "请", "translation": "пожалуйста", "language": "Chinese", "difficulty": 3},
        {"word": "朋友", "translation": "друг", "language": "Chinese", "difficulty": 3},
        {"word": "学习", "translation": "учиться", "language": "Chinese", "difficulty": 3},
        
        # Русский язык (для иностранцев)
        {"word": "привет", "translation": "hello", "language": "Russian", "difficulty": 1},
        {"word": "спасибо", "translation": "thank you", "language": "Russian", "difficulty": 1},
        {"word": "пожалуйста", "translation": "please", "language": "Russian", "difficulty": 2},
        {"word": "до свидания", "translation": "goodbye", "language": "Russian", "difficulty": 3},
        {"word": "красота", "translation": "beauty", "language": "Russian", "difficulty": 3},
        {"word": "дружба", "translation": "friendship", "language": "Russian", "difficulty": 4},
    ]
    
    # Создаем слова с разными датами для графика
    today = datetime.now()
    added_words = 0
    
    print("📝 Добавление слов...")
    for i, word_data in enumerate(words_data):
        try:
            # Создаем слово с рандомной датой в прошлом для тестирования графика
            days_ago = i % 7  # Распределяем по последним 7 дням
            created_date = today - timedelta(days=days_ago)
            
            word = Word(
                word=word_data["word"],
                translation=word_data["translation"],
                language=word_data["language"],
                difficulty=word_data["difficulty"],
                created_at=created_date
            )
            
            # Для некоторых слов добавляем дату изучения
            if word_data["difficulty"] >= 4:
                review_date = created_date + timedelta(days=1)
                word.last_reviewed = review_date
                
                # Добавляем слово и отмечаем как изученное
                word_id = db.add_word(word)
                db.mark_as_learned(word_id)
            else:
                db.add_word(word)
            
            added_words += 1
            print(f"  ✓ {word_data['word']} ({word_data['language']})")
            
        except Exception as e:
            print(f"  ✗ Ошибка при добавлении {word_data['word']}: {e}")
    
    # Получаем и выводим статистику
    progress = db.get_user_progress()
    
    print("\n✅ Заполнение завершено!")
    print(f"📊 Статистика:")
    print(f"   Всего слов: {progress.total_words}")
    print(f"   Изучено слов: {progress.learned_words}")
    print(f"   Прогресс: {progress.get_progress_percentage():.1f}%")
    print(f"   Серия дней: {progress.streak_days}")
    
    # Выводим количество слов по языкам
    print(f"\n🌍 Распределение по языкам:")
    for language in settings.SUPPORTED_LANGUAGES:
        words = db.get_words_by_language(language)
        if words:
            learned = sum(1 for w in words if w.difficulty >= 4)
            print(f"   {language}: {len(words)} слов ({learned} изучено)")
    
    return added_words

if __name__ == "__main__":
    try:
        count = seed_database()
        print(f"\n🎉 База данных успешно заполнена {count} словами!")
        print(f"📍 Путь к БД: {settings.DATABASE_PATH}")
        print("\nТеперь вы можете запустить приложение: python main.py")
    except Exception as e:
        print(f"❌ Ошибка при заполнении БД: {e}")
        sys.exit(1)