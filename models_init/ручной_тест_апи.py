import os

import requests

API_URL = "http://localhost:8000/process"  # URL сервера FastAPI
IMAGE_PATH = r"C:\Users\andre\OneDrive\Рабочий стол\data\photo_2025-12-19_06-38-24.jpg"  # путь к тестовому изображению

def send_image_for_json(image_path: str):
    try:
        with open(image_path, "rb") as f:
            files = {"file": (image_path, f, "image/png")}
            response = requests.post(API_URL, files=files, timeout=300)

        if response.status_code == 200:
            print("✅ JSON успешно получен:")
            print(response.json())
        else:
            print(f"❌ Ошибка {response.status_code}:")
            print(response.json())
            print(response)
            print(response.text)

    except Exception as e:
        print("❌ Ошибка при отправке изображения:", e)

if __name__ == "__main__":
    import time
    dir_path = r"C:\Users\andre\OneDrive\Рабочий стол\data"
    d = os.listdir(dir_path)
    for i in d:
        print(i)
        im_path = os.path.join(dir_path, i)
        st = time.time()
        send_image_for_json(im_path)
        print(time.time() - st)
