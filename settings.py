import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Класс для хранения настроек бота"""
    
    # Токен бота Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Название бота (для логов)
    BOT_NAME: str = "Smart Support Bot"
    
    @property
    def is_valid(self) -> bool:
        """Проверка, что все обязательные настройки заполнены"""
        return bool(self.BOT_TOKEN)


# Глобальный объект настроек
settings = Settings()
