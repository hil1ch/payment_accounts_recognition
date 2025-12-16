FROM python:3.11.9-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /backend/

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

ENV PATH="/backend/.venv/bin:$PATH"

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

ENV PYTHONPATH=/app

COPY . /backend

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync
    
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]