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
from core.logging_config import logger


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
        try:
            logger.info(f"Initializing models (OCR: {settings.ocr_model_type}, LLM: {settings.llm_model_type})")
            
            # Парсим языки для OCR из строки конфига
            if settings.ocr_languages != None:
                languages = [lang.strip() for lang in settings.ocr_languages.split(",")]
            else:
                languages = None
            
            # Создаем OCR модель через фабрику
            self.ocr_model: OCRModel = create_ocr_model(
                model_type=settings.ocr_model_type,
                languages=languages,
                gpu=settings.ocr_gpu
            )
            logger.info(f"OCR model initialized (languages: {languages}, GPU: {settings.ocr_gpu})")
            
            # Создаем LLM модель через фабрику
            self.llm_model: LLMModel = create_llm_model(
                model_type=settings.llm_model_type,
                base_url=settings.ollama_host,
                model_name=settings.ollama_model_name
            )
            logger.info(f"LLM model initialized (model: {settings.ollama_model_name})")
        except Exception as e:
            logger.error(f"Failed to initialize models: {str(e)}")
            raise
    
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
        try:
            prompt = self._read_prompt().replace("{{DOCUMENT_MARKDOWN}}", text)
            logger.debug("Generating JSON with LLM...")
            
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
            
            generation_time = result.get("generated_time", 0)
            logger.info(f"LLM generation completed in {generation_time:.2f}s")
            logger.debug(f"LLM result: {result.get('result_text', '')}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to generate JSON with LLM: {str(e)}")
            raise
    
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
        try:
            # 1. Обрабатываем файл через OCR
            logger.info(f"Starting OCR for file: {file_path}")
            if(file_path.lower().endswith(".pdf")):
                markdown_text = self.ocr_model.extract_text_from_pdf(file_path)
            #TODO: добавить поддержку изображений других форматов
            elif(file_path.lower().endswith((".png", ".jpg", ".jpeg"))):
                markdown_text = self.ocr_model.extract_text_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
                      
            logger.info("OCR completed")
            logger.debug(f"OCR result: {markdown_text}")
            
            # 3. Очищаем текст от артефактов OCR
            cleaned_text = clean_ocr_markdown(markdown_text)
            logger.debug(f"Cleaned text: {cleaned_text}")
            
            # 4. Генерируем JSON через LLM
            llm_result = self._generate_json_from_text(cleaned_text)
            
            # 5. Парсим и валидируем JSON
            logger.debug("Repairing JSON...")
            llm_json = json_repair.repair_json(llm_result["result_text"])
            decoded_json_object = json_repair.loads(llm_json)
            logger.info("JSON parsed successfully")
            logger.debug(f"Parsed JSON: {llm_json}")
            
            return decoded_json_object
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {str(e)}")
            raise
        #TODO: добавить поддержку изображений других форматов

    def process(self, message: Json):
        """Обрабатывает сообщение из очереди.
        
        Args:
            message: JSON сообщение с job_id и file_path
        """
        job_id = None
        try:
            parsed_message = RabbitMessage.model_validate(message)
            job_id = parsed_message.job_id
            file_path = parsed_message.file_path
            
            logger.info(f"Processing job {job_id}, file: {file_path}")
            
            # Обновляем статус задачи
            self.redis_service.change_status(str(job_id), JobStatus.in_progress)
            
            # Обрабатываем документ
            result = self._process_document(str(file_path))
            
            # Сохраняем результат
            self.redis_service.save_result(str(job_id), result)
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            # В случае ошибки обновляем статус задачи
            if job_id:
                self.redis_service.change_status(str(job_id), JobStatus.failed)
            logger.error(f"Error processing job {job_id}: {str(e)}")
            raise 