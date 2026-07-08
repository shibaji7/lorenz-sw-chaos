"""Optional OMNI loader."""

from __future__ import annotations

import hashlib
import io
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
from loguru import logger


logger.debug("Loaded omni_loader module")


class OmniUnavailableError(RuntimeError):
    """Raised when OMNI data cannot be retrieved in the current environment."""


_OMNI_WEB_URL = "https://omniweb.gsfc.nasa.gov/cgi/nx1.cgi"
_STAGING_URL_RE = re.compile(r"https?://omniweb\.gsfc\.nasa\.gov/staging/omni2_[A-Za-z0-9_]+\.lst")
_DATA_LINE_RE = re.compile(r"^\s*[-+]?\d")


def _cache_root(cache_dir: Optional[str]) -> Path:
    if cache_dir:
        root = Path(cache_dir)
    else:
        root = Path.home() / ".cache" / "lorenzsw" / "omni"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _cache_key(start_iso: str, end_iso: str, index: str) -> str:
    digest = hashlib.sha256(f"{start_iso}|{end_iso}|{index}".encode("utf-8")).hexdigest()
    return digest[:16]


def _load_cached_text(cache_file: Path) -> str | None:
    if cache_file.exists():
        logger.info("Loading OMNI response from cache: {}", cache_file)
        return cache_file.read_text(encoding="utf-8")
    return None


def _store_cached_text(cache_file: Path, text: str) -> None:
    try:
        cache_file.write_text(text, encoding="utf-8")
    except OSError as exc:
        logger.warning("Failed to write OMNI cache {}: {}", cache_file, exc)


def _extract_staging_url(text: str) -> str | None:
    match = _STAGING_URL_RE.search(text)
    return match.group(0) if match else None


def _parse_datetime(row: list[float]) -> datetime:
    year = int(row[0])
    doy = int(row[1])
    hour = int(row[2]) if len(row) > 2 else 0
    minute = int(row[3]) if len(row) > 3 else 0
    second = int(row[4]) if len(row) > 4 else 0
    base = datetime(year, 1, 1, tzinfo=timezone.utc)
    return base + timedelta(days=doy - 1, hours=hour, minutes=minute, seconds=second)


def _is_data_line(line: str) -> bool:
    return bool(_DATA_LINE_RE.match(line))


def _parse_numeric_table(text: str, index: str) -> pd.DataFrame:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    data_lines = [line for line in lines if _is_data_line(line)]
    if not data_lines:
        raise OmniUnavailableError("OMNI response did not contain parseable numeric rows.")

    records: list[dict[str, float | datetime]] = []
    max_values = 0
    for line in data_lines:
        tokens = line.split()
        values = [float(token) for token in tokens]
        if len(values) < 5:
            raise OmniUnavailableError("OMNI row does not contain enough time columns.")
        time_cols = 5 if len(values) >= 6 else 4 if len(values) == 5 else 3
        timestamp = _parse_datetime(values[:time_cols])
        payload = values[time_cols:]
        max_values = max(max_values, len(payload))
        record: dict[str, float | datetime] = {"time": timestamp}
        for i, value in enumerate(payload, start=1):
            if value <= -1.0e30:
                record[f"value_{i}"] = float("nan")
            else:
                record[f"value_{i}"] = value
        records.append(record)

    frame = pd.DataFrame.from_records(records).set_index("time").sort_index()
    value_cols = [col for col in frame.columns if col.startswith("value_")]
    if not value_cols:
        raise OmniUnavailableError("OMNI response contained no data columns.")

    if len(value_cols) == 1:
        return frame.rename(columns={value_cols[0]: index})

    # If multiple values are present, keep the generic names rather than guessing
    # a scientific interpretation from the endpoint response.
    return frame


def _request_text(session: requests.Session, payload: dict[str, str], timeout: float) -> str:
    try:
        response = session.post(_OMNI_WEB_URL, data=payload, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise OmniUnavailableError(f"OMNI request failed: {exc}") from exc

    text = response.text
    staging_url = _extract_staging_url(text)
    if staging_url:
        logger.info("Fetching OMNI staging file: {}", staging_url)
        try:
            staged = session.get(staging_url, timeout=timeout)
            staged.raise_for_status()
        except requests.RequestException as exc:
            raise OmniUnavailableError(f"OMNI staging fetch failed: {exc}") from exc
        return staged.text
    return text


def load_omni_index(
    start_iso: str,
    end_iso: str,
    index: str = "SYM_H",
    cache_dir: Optional[str] = None,
    timeout: float = 30.0,
) -> pd.DataFrame:
    """Load an OMNI index time series when remote access is available.

    The loader is best-effort. It uses the OMNIWeb command-line endpoint and
    falls back to a cached payload if available. If the network is unavailable
    or the response cannot be parsed, OmniUnavailableError is raised.
    """

    logger.info("Loading OMNI index {} from {} to {}", index, start_iso, end_iso)
    cache_root = _cache_root(cache_dir)
    cache_file = cache_root / f"{index}_{_cache_key(start_iso, end_iso, index)}.txt"

    cached = _load_cached_text(cache_file)
    if cached is not None:
        return _parse_numeric_table(cached, index=index)

    payload = {
        "activity": "ftp",
        "res": "hour",
        "spacecraft": "omni2",
        "start_date": start_iso.replace("-", ""),
        "end_date": end_iso.replace("-", ""),
        "maxdays": "31",
        "vars": index,
        "scale": "Linear",
        "view": "0",
        "nsum": "1",
        "paper": "0",
        "charsize": "",
        "xstyle": "0",
        "ystyle": "0",
        "symbol": "0",
        "symsize": "",
        "linestyle": "solid",
        "table": "0",
        "imagex": "640",
        "imagey": "480",
        "color": "",
        "back": "",
    }

    logger.debug("Submitting OMNI request with payload keys: {}", sorted(payload))
    with requests.Session() as session:
        text = _request_text(session, payload, timeout=timeout)

    _store_cached_text(cache_file, text)
    return _parse_numeric_table(text, index=index)
