import pytest
import tempfile
import os
from datetime import datetime
from models import Word
from database import DatabaseManager
from exceptions import DatabaseError

class TestDatabaseManager:
    @pytest.fixture
    def db_manager(self):
        """Фикстура для создания временной БД"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        manager = DatabaseManager(db_path)
        yield manager
        
        # Очистка после тестов
        manager._get_connection().close()
        os.unlink(db_path)
    
    def test_add_word(self, db_manager):
        """Тест добавления слова"""
        word = Word(
            word="Test",
            translation="Тест",
            language="English",
            difficulty=2
        )
        
        word_id = db_manager.add_word(word)
        assert word_id is not None
        assert isinstance(word_id, int)
    
    def test_add_duplicate_word(self, db_manager):
        """Тест добавления дубликата слова"""
        word1 = Word(word="Hello", translation="Привет", language="English", difficulty=1)
        word2 = Word(word="Hello", translation="Привет", language="English", difficulty=2)
        
        db_manager.add_word(word1)
        
        with pytest.raises(DatabaseError):
            db_manager.add_word(word2)
    
    def test_get_all_words(self, db_manager):
        """Тест получения всех слов"""
        # Добавляем тестовые слова
        words_to_add = [
            Word(word="Apple", translation="Яблоко", language="English", difficulty=1),
            Word(word="Banana", translation="Банан", language="English", difficulty=2),
        ]
        
        for word in words_to_add:
            db_manager.add_word(word)
        
        words = db_manager.get_all_words()
        assert len(words) == 2
        assert words[0].word == "Banana"  # Сортировка по дате создания DESC
    
    def test_delete_word(self, db_manager):
        """Тест удаления слова"""
        word = Word(word="Test", translation="Тест", language="English", difficulty=1)
        word_id = db_manager.add_word(word)
        
        # Проверяем, что слово добавлено
        words_before = db_manager.get_all_words()
        assert len(words_before) == 1
        
        # Удаляем слово
        db_manager.delete_word(word_id)
        
        # Проверяем, что слово удалено
        words_after = db_manager.get_all_words()
        assert len(words_after) == 0
    
    def test_mark_as_learned(self, db_manager):
        """Тест отметки слова как изученного"""
        word = Word(word="Test", translation="Тест", language="English", difficulty=1)
        word_id = db_manager.add_word(word)
        
        db_manager.mark_as_learned(word_id)
        
        words = db_manager.get_all_words()
        updated_word = next(w for w in words if w.id == word_id)
        
        assert updated_word.difficulty == 5
        assert updated_word.last_reviewed is not None
    
    def test_get_user_progress(self, db_manager):
        """Тест получения прогресса пользователя"""
        progress = db_manager.get_user_progress()
        
        assert isinstance(progress.total_words, int)
        assert isinstance(progress.learned_words, int)
        assert isinstance(progress.streak_days, int)