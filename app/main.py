from fastapi import FastAPI
from app.api.router import router
from app.database import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cris")

app = FastAPI(title="CRIS - Crypto Exchange", version="1.0.0")
app.include_router(router)


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("CRIS backend started")


@app.get("/health")
async def health():
    return {"status": "ok"}