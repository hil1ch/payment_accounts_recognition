from abc import ABC, abstractmethod
from pathlib import Path

class OCRModel(ABC):
    @abstractmethod
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from the given image.

        Args:
            image_path (str): The file path to the image.
        Returns:
            str: The extracted text from the image. 
        """
        pass
    @abstractmethod
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        pass
    
    def extract_text_from_pdf_via_images(self, pdf_path: str) -> str:
        """Вспомогательный метод для конвертации PDF -> изображения -> текст."""

        import fitz  # PyMuPDF
        
        pdf_path = Path(pdf_path)
        doc = fitz.open(pdf_path)
        
        all_text_parts = []
        zoom = 300 / 72  # DPI 300
        matrix = fitz.Matrix(zoom, zoom)
        
        try:
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                
                # Создаем временный путь для изображения страницы
                temp_image_path = pdf_path.parent / f"_temp_page_{page_num}.jpg"
                pix.save(temp_image_path)
                
                try:
                    # Обрабатываем страницу через OCR
                    page_text = self.extract_text_from_image(str(temp_image_path))
                    all_text_parts.append(page_text)
                finally:
                    # Удаляем временное изображение
                    if temp_image_path.exists():
                        temp_image_path.unlink()
        
        finally:
            doc.close()
        
        return "\n".join(all_text_parts)
