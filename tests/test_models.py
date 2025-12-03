import pytest
from datetime import datetime
from models import Word, UserProgress

class TestWord:
    def test_word_creation(self):
        """Тест создания объекта Word"""
        word = Word(
            id=1,
            word="Hello",
            translation="Привет",
            language="English",
            difficulty=3
        )
        
        assert word.id == 1
        assert word.word == "Hello"
        assert word.translation == "Привет"
        assert word.language == "English"
        assert word.difficulty == 3
    
    def test_to_dict(self):
        """Тест преобразования в словарь"""
        word = Word(
            id=1,
            word="Test",
            translation="Тест",
            language="Russian",
            difficulty=2,
            last_reviewed=datetime(2024, 1, 1, 12, 0),
            created_at=datetime(2024, 1, 1)
        )
        
        result = word.to_dict()
        
        assert result["id"] == 1
        assert result["word"] == "Test"
        assert result["translation"] == "Тест"
        assert result["language"] == "Russian"
        assert result["difficulty"] == "2"
        assert "2024-01-01" in result["last_reviewed"]

class TestUserProgress:
    def test_progress_percentage(self):
        """Тест расчета процента прогресса"""
        progress = UserProgress(total_words=10, learned_words=5)
        assert progress.get_progress_percentage() == 50.0
    
    def test_progress_percentage_zero(self):
        """Тест прогресса при нуле слов"""
        progress = UserProgress(total_words=0, learned_words=0)
        assert progress.get_progress_percentage() == 0
    
    def test_progress_percentage_all_learned(self):
        """Тест прогресса при всех изученных словах"""
        progress = UserProgress(total_words=10, learned_words=10)
        assert progress.get_progress_percentage() == 100.0