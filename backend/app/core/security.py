from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth

from app.core.access_control import load_access_control_rules


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_firebase_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    """
    Verifies Firebase ID token from Authorization header.

    Expected header:
    Authorization: Bearer <firebase_id_token>
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header"
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme"
        )

    token = credentials.credentials

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token"
        )


def get_user_role(current_user: dict) -> str:
    """
    Returns admin or user based on the private access_control.csv file.
    """

    admin_emails, _ = load_access_control_rules()
    email = current_user.get("email", "").strip().lower()

    if email in admin_emails:
        return "admin"

    return "user"


def require_admin(current_user: dict):
    """
    Allows access only to admin users.
    """

    role = get_user_role(current_user)

    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return current_user


def check_user_access(current_user: dict, requested_user_id: str):
    """
    Authorization rule:
    - Admin can access all anonymized users.
    - Normal user can access only their mapped anonymized user_id.
    """

    admin_emails, user_email_to_anon_id = load_access_control_rules()
    email = current_user.get("email", "").strip().lower()

    if email in admin_emails:
        return True

    allowed_user_id = user_email_to_anon_id.get(email)

    if allowed_user_id != requested_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this user's data"
        )

    return True