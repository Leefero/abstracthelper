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
    
    # Настройки датасета
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "local")  # 'local' или 'google_sheets'
    GOOGLE_SHEET_ID: str = os.getenv("GOOGLE_SHEET_ID", "")
    GOOGLE_SHEET_NAME: str = os.getenv("GOOGLE_SHEET_NAME", "measures_sheet")
    LOCAL_DATASET_PATH: str = os.getenv("LOCAL_DATASET_PATH", "data/sample_dataset.xlsx")
    
    # Путь к credentials для Google Sheets
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    
    @property
    def is_valid(self) -> bool:
        """Проверка, что все обязательные настройки заполнены"""
        return bool(self.BOT_TOKEN)


# Глобальный объект настроек
settings = Settings()
