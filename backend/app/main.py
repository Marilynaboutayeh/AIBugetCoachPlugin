from fastapi import FastAPI
from app.api.transactions import router as transactions_router

app = FastAPI(title="AI Budget Coach Plugin")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(transactions_router)