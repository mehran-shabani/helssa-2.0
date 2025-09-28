import json
import logging
import time
from collections.abc import Mapping
from contextvars import ContextVar
from typing import Any

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
MASK_KEYS = {"password", "token", "otp", "national_code"}

def _mask(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return {k: ("***" if k in MASK_KEYS else _mask(v)) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_mask(v) for v in obj]
    return obj

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": request_id_ctx.get("-"),
        }
        if record.args and isinstance(record.args, Mapping):
            base["args"] = _mask(record.args)
        if record.__dict__.get("extra"):
            base["extra"] = _mask(record.__dict__["extra"])
        return json.dumps(base, ensure_ascii=False)

def setup_logging():
    h = logging.StreamHandler()
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [h]
    root.setLevel(logging.INFO)
