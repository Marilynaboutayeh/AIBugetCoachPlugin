from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"

print("ENV PATH:", ENV_PATH)
print("ENV FILE EXISTS:", ENV_PATH.exists())

load_dotenv(ENV_PATH, override=True)

print("MAIN OPENAI KEY EXISTS:", bool(os.getenv("OPENAI_API_KEY")))

from fastapi import FastAPI, Depends

from app.core.db import engine, Base
from app.api.transactions import router as transactions_router
from app.api.insights import router as insights_router
from app.api.forecast import router as forecast_router
from app.models.transaction import Transaction
from app.core.firebase import initialize_firebase
from app.api import chat

from app.core.security import (
    get_current_firebase_user,
    get_user_role,
    require_admin,
    check_user_access
)



# Initialize Firebase Admin SDK
initialize_firebase()


app = FastAPI(title="AI Budget Coach Plugin")

# Create tables (MVP)
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/protected-test")
def protected_test(current_user=Depends(get_current_firebase_user)):
    role = get_user_role(current_user)

    return {
        "message": "Authenticated request accepted",
        "firebase_uid": current_user.get("uid"),
        "email": current_user.get("email"),
        "role": role
    }


@app.get("/admin-test")
def admin_test(current_user=Depends(get_current_firebase_user)):
    require_admin(current_user)

    return {
        "message": "Admin access accepted",
        "email": current_user.get("email"),
        "role": get_user_role(current_user)
    }


@app.get("/user-access-test/{user_id}")
def user_access_test(
    user_id: str,
    current_user=Depends(get_current_firebase_user)
):
    check_user_access(current_user, user_id)

    return {
        "message": "User access accepted",
        "requested_user_id": user_id,
        "email": current_user.get("email"),
        "role": get_user_role(current_user)
    }


app.include_router(transactions_router)
app.include_router(insights_router)
app.include_router(forecast_router)
app.include_router(chat.router)
