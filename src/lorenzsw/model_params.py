"""Shared model parameter loading."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger


logger.debug("Loaded model_params module")

_MODEL_PARAMS_PATH = Path(__file__).with_name("model_params.json")


def load_model_params(path: str | Path | None = None) -> dict[str, Any]:
    """Load the shared model parameter JSON."""

    params_path = Path(path) if path is not None else _MODEL_PARAMS_PATH
    with params_path.open("r", encoding="utf-8") as handle:
        params = json.load(handle)
    logger.info("Loaded model parameters from {}", params_path)
    return params
