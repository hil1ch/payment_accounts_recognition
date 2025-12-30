import time
from pathlib import Path
from core.config import settings
import ollama
import json_repair
from services.cleen_up_markdown import clean_ocr_markdown
import easyocr
import fitz  # PyMuPDF


ollama.base_url = settings.ollama_host

BASE_DIR = Path(__file__).resolve().parents[2]
PROMPT_PATH = BASE_DIR / "json_prompt.txt"

MAX_GENERATION_TIME = settings.max_generation_time  # seconds

#required_models = [
#    "gemma3:4b-it-qat",
#]

#MARKDOWN_GENERATE_PROMPT_TEMPLATE = "{{IMAGE}}\n<|grounding|>Convert the document to markdown."

reader = easyocr.Reader(
    ['en', 'ru'],   # языки
    gpu=False       # CPU only
)

def read_prompt(prompt_path: str = PROMPT_PATH) -> str:
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()
    

def get_llm_answer(
    text: str,
    model_name="gemma3:4b-it-qat",
):
    prompt = read_prompt().replace("{{DOCUMENT_MARKDOWN}}", text)

    message = {
        "role": "user",
        "content": prompt,
    }

    response_stream = ollama.chat(
        model=model_name,
        messages=[message],
        stream=True,
        options={"temperature": 0.1},
    )

    start_time = time.time()
    result = ""

    for chunk in response_stream:
        if "message" in chunk and "content" in chunk["message"]:
            result += chunk["message"]["content"]

        if time.time() - start_time > MAX_GENERATION_TIME:
            break

    return {
        "result_text": result,
        "generated_time": time.time() - start_time,
    }


def get_image_text(image_path: str) -> str:
    results = reader.readtext(image_path, detail=0)
    text = "\n".join(results)
    return text


#TODO: Нужно понять как обрабатывать многостраничные PDF и переносить их в images
def single_page_pdf_to_jpg(
    pdf_path: str | Path,
    output_jpg_path: str | Path,
    dpi: int = 300) -> Path:
    pdf_path = Path(pdf_path)
    output_jpg_path = Path(output_jpg_path)

    doc = fitz.open(pdf_path)

    if doc.page_count != 1:
        raise ValueError(f"Ожидался одностраничный PDF, страниц: {doc.page_count}")

    page = doc.load_page(0)

    zoom = dpi / 72  # 72 — базовый DPI PDF
    matrix = fitz.Matrix(zoom, zoom)

    pix = page.get_pixmap(matrix=matrix, alpha=False)
    pix.save(output_jpg_path)

    doc.close()
    return output_jpg_path

def process_file(pdf_path: str):
    jpg_path = Path(pdf_path).with_suffix(".jpg")
    single_page_pdf_to_jpg(
        pdf_path=pdf_path,
        output_jpg_path=jpg_path,
        dpi=300)
    markdown_text = get_image_text(str(jpg_path))
    print(markdown_text)
    markdown_text = clean_ocr_markdown(markdown_text)
    print(markdown_text)
    print("llm_result...")
    llm_result = get_llm_answer(text=markdown_text)
    print (llm_result)
    llm_json = json_repair.repair_json(llm_result["result_text"])
    print(llm_json)
    decoded_json_object = json_repair.loads(llm_json)
    return decoded_json_object
