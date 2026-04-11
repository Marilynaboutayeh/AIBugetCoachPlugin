from fastapi import FastAPI
from app.api.categorization import router as categorization_router

app = FastAPI(title="Categorization Service")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(categorization_router, prefix="/internal", tags=["Categorization"])