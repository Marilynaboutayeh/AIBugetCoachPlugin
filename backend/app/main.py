from fastapi import FastAPI

from app.core.db import engine, Base
from app.api.transactions import router as transactions_router
from app.api.insights import router as insights_router

app = FastAPI(title="AI Budget Coach Plugin")

# Create tables (MVP)
Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(transactions_router)
app.include_router(insights_router)