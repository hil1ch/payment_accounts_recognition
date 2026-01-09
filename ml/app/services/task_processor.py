from pathlib import Path
from pydantic import Json
import json_repair
import fitz  # PyMuPDF

from services.redis_service import RedisService
from schemas.redis_message import JobStatus
from schemas.rabbit_message import RabbitMessage
from core.config import settings
from models.model_factory import create_ocr_model, create_llm_model
from models.base.ocr_model import OCRModel
from models.base.llm_model import LLMModel
from services.cleen_up_markdown import clean_ocr_markdown


class TaskProcessor:
    """Обработчик задач: извлекает текст из PDF через OCR и преобразует в JSON через LLM."""
    
    def __init__(self, redis_service: RedisService):
        """Инициализация процессора задач."""
        self.redis_service = redis_service
        
        # Инициализируем модели один раз при создании процессора
        # Это эффективнее, чем создавать их при каждой обработке
        self._init_models()
        
        # Путь к промпту для LLM
        #TODO: Вынести в настройки
        self.base_dir = Path(__file__).resolve().parents[2]
        self.prompt_path = self.base_dir / "json_prompt.txt"
    
    def _init_models(self):
        """Инициализирует OCR и LLM модели на основе конфигурации."""
        # Парсим языки для OCR из строки конфига
        languages = [lang.strip() for lang in settings.ocr_languages.split(",")]
        
        # Создаем OCR модель через фабрику
        self.ocr_model: OCRModel = create_ocr_model(
            model_type=settings.ocr_model_type,
            languages=languages,
            gpu=settings.ocr_gpu
        )
        
        # Создаем LLM модель через фабрику
        self.llm_model: LLMModel = create_llm_model(
            model_type=settings.llm_model_type,
            base_url=settings.ollama_host,
            model_name=settings.ollama_model_name
        )
    
    def _read_prompt(self) -> str:
        """Читает промпт из файла."""
        with open(self.prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    
    
    def _generate_json_from_text(self, text: str) -> dict:
        """Генерирует JSON из текста через LLM.
        
        Args:
            text: Текст документа
            
        Returns:
            dict: Результат генерации с полями result_text и generated_time
        """
        prompt = self._read_prompt().replace("{{DOCUMENT_MARKDOWN}}", text)
        
        # Передаем max_generation_time для моделей, которые его поддерживают (например, OllamaModel)
        # Модели, которые его не поддерживают, просто проигнорируют этот параметр
        try:
            result = self.llm_model.generate(
                prompt=prompt,
                max_generation_time=settings.max_generation_time
            )
        except TypeError:
            # Если модель не поддерживает max_generation_time, вызываем без него
            result = self.llm_model.generate(prompt)
        
        return result
    
    def _process_document(self, file_path: str) -> dict:
        """Обрабатывает PDF документ: извлекает текст и преобразует в JSON.
        
        Пайплайн:
        1. PDF -> JPG (конвертация)
        2. JPG -> текст (OCR)
        3. Очистка текста от артефактов OCR
        4. Текст -> JSON (LLM)
        5. Парсинг и валидация JSON
        
        Args:
            pdf_path: Путь к PDF файлу
            
        Returns:
            dict: Распарсенный JSON объект
        """
        # 1. Обрабатываем файл через OCR
        print(f"Starting OCR for file: {file_path}")
        if(file_path.lower().endswith(".pdf")):
            markdown_text = self.ocr_model.extract_text_from_pdf(file_path)
        #TODO: добавить поддержку изображений других форматов
        elif(file_path.lower().endswith((".png", ".jpg", ".jpeg"))):
            markdown_text = self.ocr_model.extract_text_from_image(file_path)
                  
        print(f"OCR result: {markdown_text}")
        
        # 3. Очищаем текст от артефактов OCR
        cleaned_text = clean_ocr_markdown(markdown_text)
        print(f"Cleaned text: {cleaned_text}")
        
        # 4. Генерируем JSON через LLM
        print("Generating JSON with LLM...")
        llm_result = self._generate_json_from_text(cleaned_text)
        print(f"LLM result: {llm_result}")
        
        # 5. Парсим и валидируем JSON
        llm_json = json_repair.repair_json(llm_result["result_text"])
        print(f"Repaired JSON: {llm_json}")
        decoded_json_object = json_repair.loads(llm_json)
        
        return decoded_json_object

    def process(self, message: Json):
        """Обрабатывает сообщение из очереди.
        
        Args:
            message: JSON сообщение с job_id и file_path
        """
        try:
            parsed_message = RabbitMessage.model_validate(message)
            job_id = parsed_message.job_id
            file_path = parsed_message.file_path
            
            # Обновляем статус задачи
            self.redis_service.change_status(str(job_id), JobStatus.in_progress)
            
            # Обрабатываем документ
            result = self._process_document(str(file_path))
            
            # Сохраняем результат
            self.redis_service.save_result(str(job_id), result)
            print(f"Processed job {job_id} with result: {result}")
            
        except Exception as e:
            # В случае ошибки обновляем статус задачи
            self.redis_service.change_status(str(job_id), JobStatus.failed)
            print(f"Error processing job {job_id}: {e}")
            raise 