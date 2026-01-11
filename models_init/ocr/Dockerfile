# --------------------------------------------------
# Базовый образ с CUDA + cuDNN для GPU
FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04
# --------------------------------------------------

# Update + нужные пакеты
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip git wget curl \
    && rm -rf /var/lib/apt/lists/*

# Python venv
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# pip обновление + vllm
RUN pip install --upgrade pip
RUN pip install vllm pillow requests pypdfium2

# рабочая директория
WORKDIR /app

# expose порт vLLM сервера
EXPOSE 8001

# команда запуска
CMD ["vllm", "serve", "lightonai/LightOnOCR-1B-1025","--limit-mm-per-prompt", "{\"image\": 1}", "--mm-processor-cache-gb", "0", "--no-enable-prefix-caching", "--gpu-memory-utilization", "0.8", "--host", "0.0.0.0", a"--port", "8001"]
