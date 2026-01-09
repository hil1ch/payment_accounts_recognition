from easyocr import Reader
from ml.app.models.base.ocr_model import OCRModel  

class EasyOCRModel(OCRModel):
    def __init__(self, languages=['en', 'ru'], gpu=False):
        """Initialize the EasyOCR reader.
        
        Args:
            languages: List of languages for OCR. Defaults to ['en'].
            gpu: Whether to use GPU for OCR. Defaults to False.
        """
        self.reader = Reader(languages, gpu=gpu)
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from the given image using EasyOCR."""
        results = self.reader.readtext(image_path, detail=0)
        return "\n".join(results)