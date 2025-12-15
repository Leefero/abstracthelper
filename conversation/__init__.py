"""
Модуль для управления диалогами (ConversationHandler)
"""

from .states import ConversationState
from .handlers import setup_conversation_handler

__all__ = ['ConversationState', 'setup_conversation_handler']
