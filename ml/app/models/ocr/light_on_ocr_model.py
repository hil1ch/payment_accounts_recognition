import base64
import requests
from pathlib import Path
from models.base.ocr_model import OCRModel
from core.logging_config import logger


class LightOnOCRModel(OCRModel):
    """OCR model using LightOn LightOnOCR via vLLM API.
    
    Connects to a vLLM server running the LightOnOCR-1B model.
    """
    
    def __init__(self, base_url: str = "http://localhost:8001", 
                 model_name: str = "lightonai/LightOnOCR-1B-1025",
                 api_key: str = None):
        """Initialize LightOnOCR model.
        
        Args:
            base_url: Base URL of the vLLM server. Defaults to "http://localhost:8001"
            model_name: Name of the LightOnOCR model. Defaults to "lightonai/LightOnOCR-1B-1025"
            api_key: Optional API key for authentication
        """
        try:
            self.base_url = base_url.rstrip("/")
            self.model_name = model_name
            self.api_key = api_key
            self.api_endpoint = f"{self.base_url}/v1/chat/completions"
            
            logger.info(f"Initializing LightOnOCRModel (base_url: {self.base_url}, model: {self.model_name})")
            
            # Test connection to vLLM server
            self._check_server_health()
            logger.info("LightOnOCRModel initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LightOnOCRModel: {str(e)}")
            raise
    
    def _check_server_health(self):
        """Check if vLLM server is accessible."""
        try:
            models_url = f"{self.base_url}/v1/models"
            response = requests.get(models_url, timeout=5)
            response.raise_for_status()
            logger.debug(f"vLLM server is healthy: {models_url}")
        except Exception as e:
            logger.warning(f"Could not verify vLLM server health: {str(e)}")
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {str(e)}")
            raise
    
    def _call_vllm_api(self, image_path: str) -> str:
        """Call vLLM API with image for OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Extracted text from the image
        """
        try:
            # Encode image to base64
            image_base64 = self._encode_image_to_base64(image_path)
            
            # Determine image media type
            file_ext = Path(image_path).suffix.lower()
            if file_ext in ['.jpg', '.jpeg']:
                media_type = "image/jpeg"
            elif file_ext == '.png':
                media_type = "image/png"
            elif file_ext in ['.webp']:
                media_type = "image/webp"
            else:
                media_type = "image/jpeg"  # Default
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_base64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "Extract all text from this image. Provide only the extracted text without any additional commentary."
                            }
                        ]
                    }
                ],
                "max_tokens": 4096,
                "temperature": 0.3
            }
            
            # Make request to vLLM API
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            logger.debug(f"Calling vLLM API for image: {image_path}")
            response = requests.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
                timeout=300
            )
            response.raise_for_status()
            
            # Extract text from response
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                text = result["choices"][0]["message"]["content"]
                logger.debug(f"Successfully extracted text from {image_path}")
                return text
            else:
                logger.warning(f"Unexpected API response structure: {result}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling vLLM API for image {image_path}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to vLLM server: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to call vLLM API: {str(e)}")
            raise
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from the given image using LightOnOCR via vLLM.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            str: Extracted text from the image
        """
        try:
            logger.debug(f"Extracting text from image: {image_path}")
            text = self._call_vllm_api(image_path)
            logger.debug(f"Extracted text from image: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from image {image_path}: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from the given PDF using LightOnOCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text from the PDF
        """
        logger.debug(f"Extracting text from PDF: {pdf_path}")
        return self.extract_text_from_pdf_via_images(pdf_path)