"""Chapman photoionization production."""

from __future__ import annotations

from typing import Callable

import numpy as np
from loguru import logger


logger.debug("Loaded chapman module")


def chapman_production(
    h_km: np.ndarray,
    t_s: float,
    P0_t: Callable[[float], float],
    h_m_km: float,
    H_km: float,
    chi_rad: float,
) -> np.ndarray:
    """Chapman photoionization production rate.

    Parameters
    ----------
    h_km:
        Altitude grid in km.
    t_s:
        Time in seconds.
    P0_t:
        Peak production rate callable.
    h_m_km, H_km, chi_rad:
        Chapman layer parameters.
    """

    h_km = np.asarray(h_km, dtype=float)
    if H_km <= 0:
        raise ValueError("H_km must be positive.")

    logger.info(
        "Computing Chapman production at t={} s over {} altitude points",
        t_s,
        h_km.size,
    )
    z = (h_km - h_m_km) / H_km
    sec_chi = 1.0 / np.cos(chi_rad)
    out = float(P0_t(t_s)) * np.exp(1.0 - z - sec_chi * np.exp(-z))
    logger.debug("Chapman production range: [{}, {}]", float(np.min(out)), float(np.max(out)))
    return out
