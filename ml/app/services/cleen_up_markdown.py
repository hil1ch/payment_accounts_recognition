import re


def clean_ocr_markdown(text):
    """
     очистка OCR-markdown от служебных тегов и типов областей
    """
    # 1. Удаляем все служебные теги <|...|>
    cleaned = re.sub(r'<\|.*?\|>', '', text, flags=re.DOTALL)

    # 2. Удаляем координаты детекции [[x,y,z,w]]
    cleaned = re.sub(r'\[\[\d+,\s*\d+,\s*\d+,\s*\d+\]\]', '', cleaned)

    # 3. Удаляем одиночные типы распознанных областей на отдельных строках
    # (image, text, table, sub_title, title, header, footer и т.д.)
    cleaned = re.sub(r'(?m)^\s*(image|text|table|sub_title|title|header|footer|paragraph|list|code)\s*$', '', cleaned)

    # 4. Удаляем остаточные символы вроде [2] в "дней[2]"
    cleaned = re.sub(r'\[\d+\]', '', cleaned)

    # 5. Удаляем пустые HTML-теги
    cleaned = re.sub(r'<[^>]*>\s*</[^>]*>', '', cleaned)

    # 6. Нормализуем пробелы и переносы строк
    # Удаляем множественные переносы строк
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    # Удаляем пробелы в начале и конце каждой строки
    cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)
    # Заменяем множественные пробелы на одинарные
    cleaned = re.sub(r'\s+', ' ', cleaned)

    # 7. Исправляем разрывы в тексте (соединяем разорванные слова и предложения)
    # Случай: "Сч. №" -> "Сч. №"
    cleaned = re.sub(r'Сч\.\s+№', 'Сч. №', cleaned)
    # Случай: "3 432,57" -> "3432,57" (числа с пробелами)
    cleaned = re.sub(r'(\d+)\s+(\d+[\.,]\d+)', r'\1\2', cleaned)
    # Случай: "ул, дом" -> "ул, дом" (соединяем разорванные адреса)
    cleaned = re.sub(r'ул,\s+дом', 'ул, дом', cleaned)
    cleaned = re.sub(r'г,\s+ул', 'г, ул', cleaned)
    # Случай: "обл, Саратов" -> "обл, Саратов"
    cleaned = re.sub(r'обл,\s+[А-Я]', lambda m: m.group(0).replace(' ', ''), cleaned)

    # 8. Удаляем остаточные пустые строки
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
    cleaned = '\n'.join(lines)

    return cleaned.strip()


# Дополнительная функция для более агрессивной очистки типов областей
def remove_area_types(text):
    """
    Дополнительное удаление типов областей
    """
    area_types = [
        'image', 'text', 'table', 'sub_title', 'title', 'header', 'footer',
        'paragraph', 'list', 'code', 'caption', 'figure', 'equation'
    ]

    # Создаем шаблон для поиска этих типов на отдельных строках
    pattern = r'(?m)^\s*(' + '|'.join(area_types) + r')\s*$'
    return re.sub(pattern, '', text)


# Финальная функция с несколькими проходами очистки
def final_clean(text):
    """
    Основная функция очистки
    """
    result = clean_ocr_markdown(text)

    result = remove_area_types(result)

    result = re.sub(r'\n{3,}', '\n\n', result)  # Максимум 2 пустые строки подряд
    result = re.sub(r'^\s+|\s+$', '', result, flags=re.MULTILINE)  # Финальная обрезка

    return result.strip()
