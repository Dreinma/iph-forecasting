import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class ModelPerformanceREST:
    """Writer model_performance via Supabase REST API."""

    def __init__(self, timeout: int = 15):
        self.base_url: Optional[str] = os.getenv("SUPABASE_URL")
        self.api_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
        self.timeout = timeout

        if not self.base_url or not self.api_key:
            raise RuntimeError("SUPABASE_URL / SUPABASE_ANON_KEY belum ter-set.")

        self.endpoint = f"{self.base_url}/rest/v1/model_performance"
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def log(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Insert satu baris ke tabel model_performance."""
        body = payload.copy()
        if "created_at" not in body:
            body["created_at"] = datetime.now(timezone.utc).isoformat()

        logger.info("  [REST] Menyimpan model_performance (%s)", body.get("model_name"))
        resp = requests.post(
            self.endpoint,
            headers=self.headers,
            json=body,
            timeout=self.timeout,
        )
        
        # ✅ ADD: Log response body untuk debug
        if resp.status_code != 201:
            logger.error(f"  [REST] Response {resp.status_code}: {resp.text}")
        
        resp.raise_for_status()
        data = resp.json()
        inserted = data[0] if isinstance(data, list) else data
        logger.info("  [REST][OK] Tersimpan dengan id=%s", inserted.get("id"))
        return inserted
