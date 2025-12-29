import os
import ollama

ollama.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")

import time
import tempfile
import json_repair

from services.cleen_up_markdown import clean_ocr_markdown

MAX_GENERATION_TIME = 200

required_models = [
    "gemma3:4b-it-qat",
]
MARKDOWN_GENERATE_PROMPT_TEMPLATE = "{{IMAGE}}\n<|grounding|>Convert the document to markdown."
FINAL_PROMPT_TEMPLATE =  '''Ты — модель для структурированного извлечения данных из финансовых документов.
Тебе передаётся текст документа в формате Markdown, полученный после OCR скана
(возможны ошибки распознавания, переносы строк, HTML-теги <br>, таблицы Markdown).

Твоя задача:
1. Извлечь ключевые данные документа.
2. Привести их к строго заданной структуре JSON.
3. Ничего не выдумывать: если данных нет — ставь null.
4. Вернуть ТОЛЬКО валидный JSON, без комментариев и пояснений.

====================================================
СТРУКТУРА И ТРЕБОВАНИЯ К JSON
====================================================

{
  "document": {
    "document_type": string,
    "document_number": string,
    "document_date": string (YYYY-MM-DD),
    "due_date": string (YYYY-MM-DD),
    "currency": string,
    "total_amount": number
  },

  "seller": {
    "legal_name": string,
    "inn": string,
    "kpp": string | null,
    "bank_account": string | null,
    "bank_bik": string | null,
    "bank_corr_account": string | null
  },

  "buyer": {
    "legal_name": string,
    "inn": string,
    "kpp": string | null
  },

  "contract_basis": {
    "basis_text": string | null,
    "contract_number": string | null,
    "contract_date": string (YYYY-MM-DD) | null
  },

  "items": [
    {
      "line_no": number,
      "description": string,
      "quantity": number,
      "unit": string,
      "price": number,
      "amount": number
    }
  ],

  "tax": {
    "vat_rate": number | null,
    "vat_amount": number | null,
    "vat_included": boolean | null
  },

  "payment": {
    "payment_purpose": string | null,
    "recipient_account": string | null,
    "recipient_bik": string | null,
    "recipient_corr_account": string | null
  },

  "system_meta": {
    "status": "issued",
    "source": "ocr"
  }
}

====================================================
ПРАВИЛА ИЗВЛЕЧЕНИЯ
====================================================

- Используй ИНН как основной идентификатор стороны.
- Денежные суммы приводи к числу с точкой в качестве разделителя.
- Если НДС указан как «Без НДС» — vat_rate = 0, vat_amount = 0, vat_included = false.
- Если указано «в т.ч. НДС» — vat_included = true.
- Дату извлекай из заголовка документа.
- Срок оплаты ищи по фразам:
  «Оплатить не позднее», «Счет действителен до», «Срок оплаты».
- Табличную часть извлекай построчно, сохраняя порядок.
- HTML-теги (<br>) и переносы строк в описаниях объединяй в один текст.

====================================================
ВХОДНЫЕ ДАННЫЕ
====================================================

{{DOCUMENT_MARKDOWN}}

====================================================
ВЫХОД
====================================================

Верни только JSON, строго соответствующий описанной структуре.
'''

def get_llm_answer(
    text: str,
    model_name="gemma3:4b-it-qat",
):
    prompt = FINAL_PROMPT_TEMPLATE.replace("{{DOCUMENT_MARKDOWN}}", text)

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

import easyocr
from PIL import Image

# Инициализируется ОДИН раз
reader = easyocr.Reader(
    ['en', 'ru'],   # языки
    gpu=False       # CPU only
)

def get_image_markdown(image_path: str) -> str:
    """
    OCR -> pseudo-markdown
    """
    results = reader.readtext(image_path, detail=0)

    # Простейший markdown
    markdown = "\n".join(results)

    return markdown

def process_file(file_path: str):
    markdown_text = get_image_markdown(file_path)
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
