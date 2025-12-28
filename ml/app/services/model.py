import os
import ollama

ollama.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")

import time
import tempfile
import json_repair

from services.cleen_up_markdown import clean_ocr_markdown

MAX_GENERATION_TIME = 200

required_models = [
    "deepseek-ocr:3b-bf16",
    "gemma3:4b-it-qat",
]
MARKDOWN_GENERATE_PROMPT_TEMPLATE = "{{IMAGE}}\n<|grounding|>Convert the document to markdown."
FINAL_PROMPT_TEMPLATE = """<тут будет текст промпта, он длинный>
{{DOCUMENT_MARKDOWN}}
"""

def get_llm_answer(
    text: str,
    model_name="gemma3:4b-it-qat",
):
    prompt = MARKDOWN_GENERATE_PROMPT_TEMPLATE.replace("{{DOCUMENT_MARKDOWN}}", text)

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

def get_image_markdown(tmp_image_path):
    model = 'deepseek-ocr:3b-bf16'

    prompt = "\n<|grounding|>Convert the document to markdown.."

    response = ollama.chat(
        model=model,
        messages=[{
            'role': 'user',
            'content': prompt,
            'images': [tmp_image_path]
        }],
        stream=False
    )
    return response['message']['content']

def process_file(file_path: str):
    markdown_text = get_image_markdown(file_path)
    print(markdown_text[:100])
    markdown_text = clean_ocr_markdown(markdown_text)
    print(markdown_text[:100])
    print("llm_result...")
    llm_result = get_llm_answer(text=markdown_text)
    print (type(llm_result))
    llm_json = json_repair.repair_json(llm_result["result_text"])
    print(llm_json)
    decoded_json_object = json_repair.loads(llm_json)
    return decoded_json_object
