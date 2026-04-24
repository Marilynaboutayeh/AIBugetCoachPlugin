import logging
from typing import Optional, Dict, Any


logger = logging.getLogger("aibudgetcoach")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(handler)


def log_api_event(
    event_type: str,
    endpoint: str,
    user_id: Optional[str] = None,
    status: str = "success",
    processing_time_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
):
    """
    Log safe API and processing events.

    IMPORTANT:
    Do not log raw merchant names, transaction amounts, full request bodies,
    or personal/private financial information.
    """
    safe_log = {
        "event_type": event_type,
        "endpoint": endpoint,
        "user_id": user_id,
        "status": status,
        "processing_time_ms": processing_time_ms,
        "extra": extra or {},
    }

    logger.info(safe_log)