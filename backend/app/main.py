from fastapi import FastAPI

app = FastAPI(title="AI Budget Coach Plugin")

@app.get("/health")
def health():
    return {"status": "ok"}