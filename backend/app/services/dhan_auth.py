"""
Dhan auth and connectivity status endpoints.
"""

from datetime import datetime
from pathlib import Path

from flask import Blueprint, jsonify

from ..utils.logger import get_logger
from .dhan_ingest import get_option_chain

logger = get_logger("mirofish.dhan_auth")

dhan_bp = Blueprint("dhan", __name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TOKEN_TIMESTAMP_FILE = PROJECT_ROOT / ".dhan_token_timestamp"


def check_token_age() -> dict:
    try:
        now = datetime.now()

        if not TOKEN_TIMESTAMP_FILE.exists():
            TOKEN_TIMESTAMP_FILE.write_text(now.isoformat(), encoding="utf-8")
            return {
                "hours_old": 0.0,
                "warning": False,
                "message": "Created token timestamp file.",
            }

        raw_timestamp = TOKEN_TIMESTAMP_FILE.read_text(encoding="utf-8").strip()
        written_at = datetime.fromisoformat(raw_timestamp)
        hours_old = max((now - written_at).total_seconds() / 3600, 0.0)
        warning = hours_old > 23

        return {
            "hours_old": round(hours_old, 2),
            "warning": warning,
            "message": "DHAN token may be expired." if warning else "DHAN token timestamp is within 23 hours.",
        }
    except Exception as exc:
        logger.warning(f"Failed to evaluate DHAN token age: {exc}")
        return {"hours_old": 0.0, "warning": True, "message": f"Unable to read token timestamp: {exc}"}


@dhan_bp.route("/status", methods=["GET"])
def dhan_status():
    token_age = check_token_age()
    chain = get_option_chain("NIFTY", 0)

    return jsonify(
        {
            "token_age": token_age,
            "chain_connected": bool(chain),
            "chain_strikes_count": len(chain),
        }
    )
