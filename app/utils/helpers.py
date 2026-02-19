"""
Utility helper functions.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def sha256_file(path: str) -> str:
    """Compute SHA-256 hash for a file."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_filename(name: str, default: str = "file") -> str:
    """Make a filename safe for filesystem usage."""
    if not name:
        return default
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return cleaned or default


def coalesce_str(value: Optional[str], fallback: str = "") -> str:
    return value if value is not None else fallback
