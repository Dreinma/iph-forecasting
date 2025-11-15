import logging
import os
from typing import Optional

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DataHandlerREST:
    """Loader data IPH melalui Supabase REST API (HTTPS)."""

    def __init__(self, timeout: int = 30):
        self.base_url: Optional[str] = os.getenv("SUPABASE_URL")
        self.api_key: Optional[str] = os.getenv("SUPABASE_ANON_KEY")
        self.timeout = timeout

        if not self.base_url or not self.api_key:
            raise RuntimeError("SUPABASE_URL atau SUPABASE_ANON_KEY belum ter-set di .env")

        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(
            "DataHandlerREST init | base_url=%s | timeout=%ss",
            self.base_url,
            self.timeout,
        )

    def load_historical_data(self) -> pd.DataFrame:
        """Mengambil data iph_data via REST API dan kembalikan DataFrame bersih."""
        endpoint = f"{self.base_url}/rest/v1/iph_data"
        params = {
            "select": "tanggal,indikator_harga",
            "order": "tanggal.asc",
        }

        try:
            logger.info("  [REST] Fetching iph_data...")
            resp = requests.get(
                endpoint,
                headers=self.headers,
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()

            rows = resp.json()
            if not rows:
                logger.warning("  [REST] Tidak ada baris yang dikembalikan Supabase")
                return pd.DataFrame(columns=["tanggal", "indikator_harga"])

            df = pd.DataFrame(rows)
            if "tanggal" not in df.columns or "indikator_harga" not in df.columns:
                logger.error(
                    "  [REST] Kolom wajib hilang. Kolom tersedia: %s",
                    list(df.columns),
                )
                return pd.DataFrame(columns=["tanggal", "indikator_harga"])

            df["tanggal"] = pd.to_datetime(df["tanggal"], errors="coerce")
            df["indikator_harga"] = pd.to_numeric(df["indikator_harga"], errors="coerce")
            df = df.dropna(subset=["tanggal", "indikator_harga"]).reset_index(drop=True)

            if df.empty:
                logger.warning("  [REST] Semua baris tidak valid setelah cleaning")
                return pd.DataFrame(columns=["tanggal", "indikator_harga"])

            logger.info(
                "  [REST][OK] Loaded %d rows | Range %s → %s",
                len(df),
                df["tanggal"].min(),
                df["tanggal"].max(),
            )
            return df

        except requests.exceptions.Timeout:
            logger.error("  [REST][ERROR] Timeout (>%ss)", self.timeout)
        except requests.exceptions.RequestException as exc:
            logger.error("  [REST][ERROR] Request gagal: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("  [REST][ERROR] Unexpected: %s", exc, exc_info=True)

        return pd.DataFrame(columns=["tanggal", "indikator_harga"])
    
