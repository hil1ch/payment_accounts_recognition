import os
import ollama
import base64
import pypdfium2 as pdfium
import io
from PIL import Image
import requests
import time
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json_repair

from cleen_up_markdown import clean_ocr_markdown

ollama.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OCR_ENDPOINT = os.getenv("OCR_HOST", "http://localhost:8001/v1/chat/completions")
OCR_MODEL = "lightonai/LightOnOCR-1B-1025"

JSON_GENERATION_MODEL_NAME = "gpt-oss:20b-cloud"

required_ollama_models = [
    JSON_GENERATION_MODEL_NAME,
]
with open("json_generation_prompt.txt", encoding='utf8') as f:
    FINAL_PROMPT_TEMPLATE = f.read()
client = ollama.Client()

def get_llm_answer(
    text: str,
):
    prompt = FINAL_PROMPT_TEMPLATE.replace("{{DOCUMENT_MARKDOWN}}", text)

    response_stream = client.generate(
        model=JSON_GENERATION_MODEL_NAME,
        prompt=prompt,
        stream=True,
    )

    start_time = time.time()
    result = []
    for chunk in response_stream:
        result.append(chunk["response"])
        print(chunk["response"], end="")
    print()
    print("Генерация JSON закончена")
    return {
        "result_text": "".join(result),
        "generated_time": time.time() - start_time,
    }

def get_image_markdown(tmp_image_path, is_pdf=False):
    print("Получение markdown изображения")
    if is_pdf:
        pdf = pdfium.PdfDocument(tmp_image_path)
        page = pdf[0]
        # Render at 200 DPI (scale factor = 200/72 ≈ 2.77)
        pil_image = page.render(scale=2.77).to_pil()
    else:
        pil_image = Image.open(tmp_image_path)
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    # Make request
    payload = {
        "model": OCR_MODEL,
        "messages": [{
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"}
            }]
        }],
        "max_tokens": 4096,
        "temperature": 0.2,
        "top_p": 0.9,
    }
    response = requests.post(OCR_ENDPOINT, json=payload, timeout=50)
    print("markdown получен")
    print(response.json())
    print(response)
    print(OCR_ENDPOINT)
    text = response.json()['choices'][0]['message']['content']
    return text
app = FastAPI(title="LLM image to json server", version="0.1")

@app.get("/health")
def health_check():
    try:
        models = ollama.list()
        model_names = [m["name"] for m in models["models"]]
        missing = [m for m in required_ollama_models if m not in model_names]

        if missing:
            return {
                "status": "degraded",
                "reason": "models_not_loaded",
                "missing_models": missing,
            }

        return {
            "status": "ok",
            "ollama": "reachable",
            "models": required_ollama_models,
        }

    except Exception as e:
        return {
            "status": "down",
            "error": str(e),
        }

@app.post("/process")
async def process_file(file: UploadFile = File(...)):
    print("Получен запрос")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не передан")

    # Проверяем расширение
    _, ext = os.path.splitext(file.filename.lower())
    if ext not in [".pdf", ".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Поддерживаются только PDF и изображения")



    # сохраняем файл во временное место
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # конвертация в markdown
        is_pdf = ext == ".pdf"
        markdown_text = get_image_markdown(tmp_path, is_pdf=is_pdf)
        markdown_text = clean_ocr_markdown(markdown_text)
        llm_result = get_llm_answer(text=markdown_text)
        llm_json = json_repair.repair_json(llm_result["result_text"])
        decoded_json_object = json_repair.loads(llm_json)

        return JSONResponse(
            decoded_json_object
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
