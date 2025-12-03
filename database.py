import sqlite3
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager

from models import Word, UserProgress
from exceptions import DatabaseError
import settings

class DatabaseManager:
    """Менеджер для работы с базой данных SQLite"""
    
    def __init__(self, db_path: str = settings.DATABASE_PATH):
        self.db_path = db_path
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для подключения к БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise DatabaseError(f"Ошибка БД: {str(e)}")
        finally:
            conn.close()
    
    def _init_database(self):
        """Инициализация таблиц БД"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица слов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    language TEXT NOT NULL,
                    difficulty INTEGER CHECK(difficulty BETWEEN 1 AND 5),
                    last_reviewed DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица прогресса пользователя
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY CHECK(id = 1),
                    total_words INTEGER DEFAULT 0,
                    learned_words INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    last_active DATETIME
                )
            ''')
            
            # Инициализация записи прогресса
            cursor.execute('''
                INSERT OR IGNORE INTO user_progress (id) VALUES (1)
            ''')
    
    def add_word(self, word: Word) -> int:
        """Добавление нового слова"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Проверка на дубликат
            cursor.execute(
                "SELECT id FROM words WHERE word = ? AND language = ?",
                (word.word, word.language)
            )
            if cursor.fetchone():
                raise DatabaseError(f"Слово '{word.word}' уже существует в языке '{word.language}'")
            
            cursor.execute('''
                INSERT INTO words (word, translation, language, difficulty, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (word.word, word.translation, word.language, word.difficulty, datetime.now()))
            
            word_id = cursor.lastrowid
            
            # Обновление статистики
            cursor.execute('''
                UPDATE user_progress 
                SET total_words = total_words + 1
                WHERE id = 1
            ''')
            
            return word_id
    
    def get_all_words(self) -> List[Word]:
        """Получение всех слов"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM words ORDER BY created_at DESC
            ''')
            
            words = []
            for row in cursor.fetchall():
                words.append(Word(
                    id=row['id'],
                    word=row['word'],
                    translation=row['translation'],
                    language=row['language'],
                    difficulty=row['difficulty'],
                    last_reviewed=datetime.fromisoformat(row['last_reviewed']) 
                        if row['last_reviewed'] else None,
                    created_at=datetime.fromisoformat(row['created_at'])
                        if row['created_at'] else None
                ))
            return words
    
    def delete_word(self, word_id: int):
        """Удаление слова по ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем слово для обновления статистики
            cursor.execute("SELECT difficulty FROM words WHERE id = ?", (word_id,))
            row = cursor.fetchone()
            if not row:
                raise DatabaseError(f"Слово с ID {word_id} не найдено")
            
            cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
            
            # Обновляем статистику
            if row['difficulty'] >= 4:  # Если слово было изучено
                cursor.execute('''
                    UPDATE user_progress 
                    SET learned_words = learned_words - 1,
                        total_words = total_words - 1
                    WHERE id = 1
                ''')
            else:
                cursor.execute('''
                    UPDATE user_progress 
                    SET total_words = total_words - 1
                    WHERE id = 1
                ''')
    
    def mark_as_learned(self, word_id: int):
        """Отметить слово как изученное"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            
            cursor.execute('''
                UPDATE words 
                SET last_reviewed = ?, difficulty = 5
                WHERE id = ?
            ''', (now, word_id))
            
            # Обновление статистики
            cursor.execute('''
                UPDATE user_progress 
                SET learned_words = learned_words + 1,
                    last_active = ?
                WHERE id = 1
            ''', (now,))
            
            # Проверка и обновление серии дней
            cursor.execute("SELECT last_active FROM user_progress WHERE id = 1")
            result = cursor.fetchone()
            if result and result['last_active']:
                last_active = datetime.fromisoformat(result['last_active'])
                if (now.date() - last_active.date()).days == 1:
                    cursor.execute('''
                        UPDATE user_progress 
                        SET streak_days = streak_days + 1
                        WHERE id = 1
                    ''')
                elif (now.date() - last_active.date()).days > 1:
                    cursor.execute('''
                        UPDATE user_progress 
                        SET streak_days = 1
                        WHERE id = 1
                    ''')
    
    def get_user_progress(self) -> UserProgress:
        """Получение прогресса пользователя"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_progress WHERE id = 1")
            row = cursor.fetchone()
            
            return UserProgress(
                total_words=row['total_words'],
                learned_words=row['learned_words'],
                streak_days=row['streak_days'],
                last_active=datetime.fromisoformat(row['last_active']) 
                    if row['last_active'] else None
            )
    
    def get_words_by_language(self, language: str) -> List[Word]:
        """Получение слов по языку"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM words 
                WHERE language = ? 
                ORDER BY difficulty DESC
            ''', (language,))
            
            words = []
            for row in cursor.fetchall():
                words.append(Word(
                    id=row['id'],
                    word=row['word'],
                    translation=row['translation'],
                    language=row['language'],
                    difficulty=row['difficulty']
                ))
            return words
    
    def get_daily_stats(self, days: int = 7) -> List[dict]:
        """Получение статистики за последние дни"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем количество добавленных слов по дням
            cursor.execute('''
                SELECT 
                    DATE(created_at) as date,
                    COUNT(*) as added_count,
                    SUM(CASE WHEN difficulty >= 4 THEN 1 ELSE 0 END) as learned_count
                FROM words 
                WHERE created_at >= date('now', ?)
                GROUP BY DATE(created_at)
                ORDER BY date
            ''', (f'-{days} days',))
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'date': row['date'],
                    'added': row['added_count'],
                    'learned': row['learned_count']
                })
            
            return stats