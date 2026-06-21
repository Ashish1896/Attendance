"""
database/supabase_client.py
============================
Supabase client singleton with connection retry and error handling.
"""

import os
import time
import logging
from functools import lru_cache
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
logger = logging.getLogger(__name__)


class SupabaseClientError(Exception):
    """Raised when Supabase client cannot be initialized."""


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Returns a cached Supabase client instance.
    Uses the service role key to bypass RLS for backend operations.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

    if not url or not key:
        raise SupabaseClientError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. "
            "Please check your .env file."
        )

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            client = create_client(url, key)
            logger.info("✅ Supabase client initialized successfully.")
            return client
        except Exception as exc:
            logger.warning(f"Supabase connect attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(1.5 * attempt)

    raise SupabaseClientError(
        f"Failed to connect to Supabase after {max_retries} attempts."
    )


def get_db() -> Client:
    """Convenience alias for get_supabase_client()."""
    return get_supabase_client()
