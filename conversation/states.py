"""
Определения состояний ConversationHandler
"""

from enum import Enum, auto


class ConversationState(Enum):
    """Состояния диалога с пользователем"""
    
    START = auto()      # Начало диалога, ожидание запроса
    SEARCH = auto()     # Обработка результатов поиска
    CONSULT = auto()    # Уточняющий диалог по выбранной мере
    FEEDBACK = auto()   # Сбор обратной связи
    
    @classmethod
    def get_all_states(cls):
        """Получить все состояния"""
        return [state.value for state in cls]
    
    def __str__(self):
        return self.name
