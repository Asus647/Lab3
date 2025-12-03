# Пользовательские исключения

class LanguageAppError(Exception):
    """Базовое исключение приложения"""
    pass

class EmptyFieldError(LanguageAppError):
    """Исключение при пустых полях ввода"""
    def __init__(self, field_name):
        super().__init__(f"Поле '{field_name}' не может быть пустым")

class DatabaseError(LanguageAppError):
    """Исключение при ошибках работы с БД"""
    pass

class InvalidDifficultyError(LanguageAppError):
    """Исключение при некорректной сложности"""
    def __init__(self, value):
        super().__init__(f"Сложность должна быть от 1 до 5, получено: {value}")

class WordNotFoundError(LanguageAppError):
    """Исключение при отсутствии слова"""
    pass