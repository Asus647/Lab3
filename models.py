from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Word:
    """Класс для представления слова"""
    id: Optional[int] = None
    word: str = ""
    translation: str = ""
    language: str = ""
    difficulty: int = 1
    last_reviewed: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self):
        """Преобразование в словарь для таблицы"""
        return {
            "id": self.id,
            "word": self.word,
            "translation": self.translation,
            "language": self.language,
            "difficulty": str(self.difficulty),
            "last_reviewed": self.last_reviewed.strftime("%Y-%m-%d %H:%M") 
                if self.last_reviewed else "Не изучено",
            "created_at": self.created_at.strftime("%Y-%m-%d") 
                if self.created_at else ""
        }

@dataclass
class UserProgress:
    """Класс для отслеживания прогресса пользователя"""
    total_words: int = 0
    learned_words: int = 0
    streak_days: int = 0
    last_active: Optional[datetime] = None
    
    def get_progress_percentage(self):
        """Получить процент изученных слов"""
        if self.total_words == 0:
            return 0
        return (self.learned_words / self.total_words) * 100