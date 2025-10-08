from fastapi import FastAPI, APIRouter, HTTPException
from api.v1 import recognition

router = APIRouter(prefix="/api/v1")
router.include_router(recognition.router)

app = FastAPI(
    title="Система распознавания содержании платёжного документа",
    version="1.0.0",
    description="""В жизненном цикле предприятия очень важную роль занимает учет финансовых трат. Порой необходимо вести статистику не всего содержимого платежных счетов, а значений конкретных полей, что требует довольно большого количества времени на чтение массива интересующих счетов и запись значений интересующих полей.
                Предлагается реализовать сервис, автоматизирующий распознавание содержимого платежного счёта. Интерфейсом взаимодействия пользователя и сервиса является телеграмм-бот.""",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(router)

@app.get("/healthcheck")
async def healthcheck():
    if True:
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=500, detail="Internal Server Error")