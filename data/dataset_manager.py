import pandas as pd
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DatasetManager:
    """Менеджер для работы с датасетом мер поддержки"""
    
    def __init__(self, data_source: str = "google_sheets"):
        """
        Инициализация менеджера датасета
        
        Args:
            data_source: источник данных ('google_sheets' или 'local')
        """
        self.data_source = data_source
        self.dataset: Optional[pd.DataFrame] = None
        self.last_loaded: Optional[datetime] = None
        self.columns_info: Dict[str, Any] = {}
        
    def load_from_google_sheets(self, sheet_id: str, sheet_name: str) -> pd.DataFrame:
        """
        Загрузка данных из Google Sheets
        
        Args:
            sheet_id: ID Google Sheets документа
            sheet_name: название листа
            
        Returns:
            pandas DataFrame с данными
        """
        try:
            logger.info(f"Загрузка данных из Google Sheets: {sheet_id}/{sheet_name}")
            
            # Для локальной разработки - заглушка
            # В реальной реализации здесь будет код для работы с gspread
            
            # Создаем тестовый датасет для разработки
            test_data = {
                'id': [1, 2, 3, 4, 5],
                'Название': [
                    'Субсидия на открытие малого бизнеса',
                    'Грант для ИП в сфере услуг',
                    'Льготный кредит на оборудование',
                    'Поддержка сельхозпроизводителей',
                    'Программа "Стартап-навигатор"'
                ],
                'Описание': [
                    'Финансовая поддержка для начинающих предпринимателей',
                    'Безвозмездная помощь индивидуальным предпринимателям',
                    'Кредитование по сниженной ставке для закупки техники',
                    'Меры поддержки для фермеров и сельхозпредприятий',
                    'Акселерационная программа для технологических стартапов'
                ],
                'Категория': ['Финансы', 'Финансы', 'Финансы', 'Сельское хозяйство', 'Инновации'],
                'Размер поддержки': ['до 500 000 руб.', 'до 1 000 000 руб.', 'до 5 000 000 руб.', 'индивидуально', 'до 3 000 000 руб.'],
                'Условия': ['Стаж ИП не менее 6 мес.', 'Оборот менее 10 млн руб.', 'Собственное обеспечение 30%', 'Наличие земельного участка', 'Инновационный продукт'],
                'Список документов': ['Заявление, паспорт, бизнес-план', 'Заявление, выписка из ЕГРИП', 'Заявление, документы на оборудование', 'Заявление, правоустанавливающие документы', 'Заявление, презентация проекта'],
                'Контакты': ['support@business.ru', 'grant@ip-center.ru', 'credit@bank-support.ru', 'agro@ministry.ru', 'startup@gov.ru'],
                'Срок подачи': ['до 31.12.2023', 'круглогодично', 'круглогодично', 'до 15.11.2023', 'до 01.12.2023'],
                'Ссылка': ['https://example.com/1', 'https://example.com/2', 'https://example.com/3', 'https://example.com/4', 'https://example.com/5']
            }
            
            df = pd.DataFrame(test_data)
            logger.info(f"Загружено {len(df)} записей из Google Sheets")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке из Google Sheets: {e}")
            # Возвращаем пустой датасет для продолжения работы
            return pd.DataFrame()
    
    def load_from_local(self, filepath: str) -> pd.DataFrame:
        """
        Загрузка данных из локального файла
        
        Args:
            filepath: путь к локальному файлу (xlsx, csv)
            
        Returns:
            pandas DataFrame с данными
        """
        try:
            logger.info(f"Загрузка данных из локального файла: {filepath}")
            
            if filepath.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            elif filepath.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:
                raise ValueError(f"Неподдерживаемый формат файла: {filepath}")
            
            logger.info(f"Загружено {len(df)} записей из локального файла")
            return df
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке из локального файла: {e}")
            raise
    
    def load_dataset(self, **kwargs) -> bool:
        """
        Основной метод загрузки датасета
        
        Returns:
            True если загрузка успешна, False в противном случае
        """
        try:
            if self.data_source == 'google_sheets':
                sheet_id = kwargs.get('sheet_id')
                sheet_name = kwargs.get('sheet_name', 'measures_sheet')
                if not sheet_id:
                    logger.warning("Не указан sheet_id для Google Sheets, используем тестовые данные")
                    self.dataset = self._create_test_dataset()
                else:
                    self.dataset = self.load_from_google_sheets(sheet_id, sheet_name)
            
            elif self.data_source == 'local':
                filepath = kwargs.get('filepath')
                if not filepath:
                    logger.warning("Не указан filepath для локального файла, используем тестовые данные")
                    self.dataset = self._create_test_dataset()
                else:
                    self.dataset = self.load_from_local(filepath)
            
            else:
                logger.warning(f"Неизвестный источник данных: {self.data_source}, используем тестовые данные")
                self.dataset = self._create_test_dataset()
            
            # Проверяем и очищаем данные
            self._clean_and_validate()
            
            # Анализируем колонки
            self._analyze_columns()
            
            self.last_loaded = datetime.now()
            logger.info(f"Датасет успешно загружен. Записей: {len(self.dataset)}, колонок: {len(self.dataset.columns)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при загрузке датасета: {e}")
            return False
    
    def _create_test_dataset(self) -> pd.DataFrame:
        """Создание тестового датасета для разработки"""
        logger.info("Создание тестового датасета")
        
        test_data = {
            'id': list(range(1, 11)),
            'Название': [f'Тестовая мера поддержки {i}' for i in range(1, 11)],
            'Описание': [f'Описание тестовой меры поддержки {i} для разработки' for i in range(1, 11)],
            'Категория': ['Финансы', 'Инновации', 'Экспорт', 'Финансы', 'Инновации', 
                         'Сельское хозяйство', 'Экспорт', 'Финансы', 'Инновации', 'Образование'],
            'Размер поддержки': ['до 1 млн руб.', 'до 3 млн руб.', 'до 5 млн руб.', 
                                'до 2 млн руб.', 'до 4 млн руб.', 'индивидуально',
                                'до 6 млн руб.', 'до 1.5 млн руб.', 'до 3.5 млн руб.', 'до 800 тыс. руб.'],
            'Статус': ['Активна', 'Активна', 'Завершена', 'Активна', 'Активна',
                      'Активна', 'Активна', 'Завершена', 'Активна', 'Активна']
        }
        
        return pd.DataFrame(test_data)
    
    def _clean_and_validate(self):
        """Очистка и валидация данных"""
        if self.dataset is None or self.dataset.empty:
            logger.warning("Датасет пустой")
            return
        
        # Удаляем полностью пустые строки
        initial_count = len(self.dataset)
        self.dataset = self.dataset.dropna(how='all')
        
        # Заполняем пропущенные значения в важных колонках
        if 'Название' in self.dataset.columns:
            self.dataset['Название'] = self.dataset['Название'].fillna('Без названия')
        
        if 'Описание' in self.dataset.columns:
            self.dataset['Описание'] = self.dataset['Описание'].fillna('Нет описания')
        
        cleaned_count = len(self.dataset)
        if cleaned_count < initial_count:
            logger.info(f"Удалено {initial_count - cleaned_count} пустых строк")
    
    def _analyze_columns(self):
        """Анализ структуры колонок датасета"""
        if self.dataset is None:
            return
        
        self.columns_info = {
            'total_columns': len(self.dataset.columns),
            'total_rows': len(self.dataset),
            'column_names': list(self.dataset.columns),
            'column_types': {col: str(self.dataset[col].dtype) for col in self.dataset.columns},
            'text_columns': [col for col in self.dataset.columns 
                           if self.dataset[col].dtype == 'object' and col not in ['id']]
        }
        
        logger.info(f"Колонки датасета: {self.columns_info['column_names']}")
        logger.info(f"Текстовые колонки для поиска: {self.columns_info['text_columns']}")
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Получение информации о загруженном датасете"""
        if self.dataset is None:
            return {'status': 'not_loaded', 'message': 'Датасет не загружен'}
        
        return {
            'status': 'loaded',
            'rows': len(self.dataset),
            'columns': len(self.dataset.columns),
            'last_loaded': self.last_loaded.isoformat() if self.last_loaded else None,
            'columns_info': self.columns_info
        }
    
    def get_sample_data(self, n: int = 3) -> list:
        """Получение сэмпла данных"""
        if self.dataset is None or self.dataset.empty:
            return []
        
        return self.dataset.head(n).to_dict('records')


# Глобальный экземпляр менеджера датасета
dataset_manager = DatasetManager(data_source='local')
