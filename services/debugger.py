from __future__ import annotations

import json
import os
from collections import deque
from datetime import datetime
from logging.handlers import RotatingFileHandler
import logging
from typing import Any, Dict, Optional


class PrismaDebugger:
    """Centralized lightweight debugger and diagnostics for the app.

    Features:
    - Structured logging to file (data/debug.log) with rotation
    - In-memory ring buffer of recent events and errors (for quick API access)
    - Helper methods to log events/errors with contextual payloads (safe JSON)
    - Verbose switch to control noise
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger("prisma")
        self.logger.setLevel(logging.INFO)
        self.recent_events: deque[Dict[str, Any]] = deque(maxlen=500)
        self.recent_errors: deque[Dict[str, Any]] = deque(maxlen=200)
        self.verbose: bool = True

    def init_app(self, app) -> None:
        log_dir = os.path.join("data")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "debug.log")

        if not any(isinstance(h, RotatingFileHandler) for h in self.logger.handlers):
            handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")
            fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
            handler.setFormatter(fmt)
            self.logger.addHandler(handler)

        # Basic request tracing
        @app.before_request
        def _before_request():  # type: ignore
            try:
                from flask import request
                if self.verbose:
                    self.event(
                        "request_start",
                        {
                            "method": request.method,
                            "path": request.path,
                            "args": request.args.to_dict(flat=True),
                        },
                    )
            except Exception:  # pragma: no cover - never fail app on debugger
                pass

    def _serialize(self, payload: Any) -> str:
        try:
            return json.dumps(payload, default=str, ensure_ascii=False)
        except Exception:
            return str(payload)

    def event(self, tag: str, data: Optional[Dict[str, Any]] = None, level: str = "INFO") -> None:
        record = {
            "time": datetime.utcnow().isoformat(),
            "tag": tag,
            "data": data or {},
            "level": level,
        }
        self.recent_events.append(record)
        self.logger.log(getattr(logging, level, logging.INFO), f"{tag} | {self._serialize(data or {})}")

    def error(self, tag: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        payload = {"message": message}
        if data:
            payload.update(data)
        record = {
            "time": datetime.utcnow().isoformat(),
            "tag": tag,
            "data": payload,
        }
        self.recent_errors.append(record)
        self.logger.error(f"{tag} | {self._serialize(payload)}")

    def record_exception(self, e: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        self.error(e.__class__.__name__, str(e), context or {})

    def get_recent(self) -> Dict[str, Any]:
        return {
            "events": list(self.recent_events)[-50:],
            "errors": list(self.recent_errors)[-50:],
            "verbose": self.verbose,
        }


debugger = PrismaDebugger()


def init_debugger(app) -> None:
    debugger.init_app(app)


def log_event(tag: str, data: Optional[Dict[str, Any]] = None, level: str = "INFO") -> None:
    debugger.event(tag, data, level)


def log_error(tag: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
    debugger.error(tag, message, data)


def record_exception(e: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    debugger.record_exception(e, context)


