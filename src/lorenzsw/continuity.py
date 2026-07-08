"""Continuity-equation drift."""

from __future__ import annotations

import numpy as np
from loguru import logger


logger.debug("Loaded continuity module")


def continuity_drift(
    n: np.ndarray,
    P_solar: np.ndarray,
    P_precip: np.ndarray,
    alpha_cm3s: float,
    beta_s: float,
) -> np.ndarray:
    """Deterministic continuity-equation drift.

    Returns
    -------
    np.ndarray
        ``P_solar + P_precip - alpha*n^2 - beta*n`` with broadcasting.
    """

    n = np.asarray(n, dtype=float)
    P_solar = np.asarray(P_solar, dtype=float)
    P_precip = np.asarray(P_precip, dtype=float)
    logger.info("Computing continuity drift for {} altitude points", n.size)
    out = P_solar + P_precip - alpha_cm3s * n**2 - beta_s * n
    logger.debug("Continuity drift range: [{}, {}]", float(np.min(out)), float(np.max(out)))
    return out
