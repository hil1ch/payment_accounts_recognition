from models.base.ocr_model import OCRModel


class MockOCRModel(OCRModel):
    """Моковая модель OCR для разработки. Возвращает фиксированный текст."""
    
    def __init__(self, mock_text: str = "Sample OCR Text\nLine 2\nLine 3"):
        """Initialize mock OCR model.
        
        Args:
            mock_text: Текст, который будет возвращаться при OCR. 
                      По умолчанию возвращает простой пример.
        """
        self.mock_text = mock_text
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Возвращает фиксированный текст вместо реального OCR."""
        return self.mock_text

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Возвращает фиксированный текст вместо реального OCR для PDF."""
        return self.mock_text
