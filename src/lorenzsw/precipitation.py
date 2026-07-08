"""Precipitation production models."""

from __future__ import annotations

from typing import Callable, Protocol, Union

import numpy as np
from loguru import logger


logger.debug("Loaded precipitation module")


class PrecipitationModel(Protocol):
    def __call__(self, h_km: np.ndarray, t_s: float) -> np.ndarray:
        """Returns production rate [cm^-3 s^-1], shape (Nh,)."""


PeakAltitude = Union[float, Callable[[float], float]]


def _resolve_peak_altitude(h_p_km: PeakAltitude, t_s: float) -> float:
    if callable(h_p_km):
        logger.debug("Resolving time-varying precipitation peak altitude at t={} s", t_s)
        return float(h_p_km(t_s))
    return float(h_p_km)


def gaussian_precipitation(
    h_km: np.ndarray,
    t_s: float,
    Q0_t: Callable[[float], float],
    h_p_km: PeakAltitude,
    H_p_km: float,
    delta_eps_ion_eV: float = 35.0,
) -> np.ndarray:
    """Gaussian precipitation production profile.

    The profile is normalized so that integrating over altitude and multiplying
    by ``delta_eps_ion_eV`` approximately recovers ``Q0_t(t_s)``.
    ``h_p_km`` may be a constant peak altitude or a callable ``h_p_km(t_s)``.
    """

    h_km = np.asarray(h_km, dtype=float)
    if H_p_km <= 0:
        raise ValueError("H_p_km must be positive.")
    if delta_eps_ion_eV <= 0:
        raise ValueError("delta_eps_ion_eV must be positive.")

    logger.info(
        "Computing precipitation proxy at t={} s over {} altitude points",
        t_s,
        h_km.size,
    )
    h_p_value = _resolve_peak_altitude(h_p_km, t_s)
    norm = delta_eps_ion_eV * np.sqrt(2.0 * np.pi) * H_p_km
    exponent = -0.5 * ((h_km - h_p_value) / H_p_km) ** 2
    out = float(Q0_t(t_s)) / norm * np.exp(exponent)
    logger.debug("Precipitation proxy range: [{}, {}]", float(np.min(out)), float(np.max(out)))
    return out
