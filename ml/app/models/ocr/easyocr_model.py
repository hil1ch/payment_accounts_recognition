from easyocr import Reader
from models.base.ocr_model import OCRModel
from core.logging_config import logger  

class EasyOCRModel(OCRModel):
    def __init__(self, languages=['en', 'ru'], gpu=False):
        """Initialize the EasyOCR reader.
        
        Args:
            languages: List of languages for OCR. Defaults to ['en'].
            gpu: Whether to use GPU for OCR. Defaults to False.
        """
        try:
            logger.info(f"Initializing EasyOCR (languages: {languages}, GPU: {gpu})")
            self.reader = Reader(languages, gpu=gpu)
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {str(e)}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from the given image using EasyOCR."""
        try:
            logger.debug(f"Extracting text from image: {image_path}")
            results = self.reader.readtext(image_path, detail=0)
            text = "\n".join(results)
            logger.debug(f"Extracted {len(results)} text blocks from image")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from image {image_path}: {str(e)}")
            raise

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from the given PDF using EasyOCR."""
        logger.debug(f"Extracting text from PDF: {pdf_path}")
        return self.extract_text_from_pdf_via_images(pdf_path)