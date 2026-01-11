import base64
import requests
import pypdfium2 as pdfium
import io

ENDPOINT = "http://localhost:8001/v1/chat/completions"
MODEL = "lightonai/LightOnOCR-1B-1025"

# Download PDF from arXiv


# Open PDF and convert first page to image
pdf = pdfium.PdfDocument(r"C:\Users\andre\OneDrive\Рабочий стол\data\168935.pdf")
page = pdf[0]
# Render at 200 DPI (scale factor = 200/72 ≈ 2.77)
pil_image = page.render(scale=2.77).to_pil()

# Convert to base64
buffer = io.BytesIO()
pil_image.save(buffer, format="PNG")
image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

# Make request
payload = {
    "model": MODEL,
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
import time
st = time.time()
response = requests.post(ENDPOINT, json=payload)
print(time.time() - st)
text = response.json()['choices'][0]['message']['content']
print(text)