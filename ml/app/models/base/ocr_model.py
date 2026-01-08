from abc import ABC, abstractmethod

class OCRModel(ABC):
    @abstractmethod
    def extract_text(self, image_path: str) -> str:
        """Extract text from the given image.

        Args:
            image_path (str): The file path to the image.
        Returns:
            str: The extracted text from the image. 
        """
        pass