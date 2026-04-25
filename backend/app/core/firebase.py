import os
import firebase_admin
from firebase_admin import credentials


def initialize_firebase():
    """
    Initializes Firebase Admin SDK once.
    Used by FastAPI to verify Firebase ID tokens.
    """

    if firebase_admin._apps:
        return

    service_account_path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        "firebase-service-account.json"
    )

    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)