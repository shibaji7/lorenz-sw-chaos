"""Lyapunov and predictability utilities."""

from __future__ import annotations

import numpy as np
from loguru import logger


logger.debug("Loaded lyapunov module")


def estimate_lyapunov(
    ensemble: np.ndarray,
    t_grid_s: np.ndarray,
    h_index: int = 0,
) -> tuple[float, np.ndarray]:
    """Estimate a Lyapunov exponent from ensemble divergence.

    The estimate is obtained by computing the mean pairwise separation at the
    specified altitude index, taking the log, and fitting a line to the portion
    of the curve after the initial time point.
    """

    ensemble = np.asarray(ensemble, dtype=float)
    t_grid_s = np.asarray(t_grid_s, dtype=float)
    if ensemble.ndim != 3:
        raise ValueError("ensemble must have shape (n_members, Nt, Nh).")
    if t_grid_s.ndim != 1:
        raise ValueError("t_grid_s must be one-dimensional.")
    if ensemble.shape[1] != t_grid_s.size:
        raise ValueError("ensemble and t_grid_s must agree along time.")
    if not (0 <= h_index < ensemble.shape[2]):
        raise ValueError("h_index is out of range.")
    if t_grid_s.size < 2:
        raise ValueError("t_grid_s must contain at least two points.")

    logger.info(
        "Estimating Lyapunov exponent from {} members over {} time points",
        ensemble.shape[0],
        ensemble.shape[1],
    )
    x = ensemble[:, :, h_index]
    n_members = x.shape[0]
    mean_log_divergence = np.full(t_grid_s.size, np.nan, dtype=float)

    for k in range(t_grid_s.size):
        values = x[:, k]
        diffs = values[:, None] - values[None, :]
        if n_members > 1:
            iu = np.triu_indices(n_members, k=1)
            distances = np.abs(diffs[iu])
            distances = distances[distances > 0]
            if distances.size > 0:
                mean_log_divergence[k] = float(np.mean(np.log(distances)))

    valid = np.isfinite(mean_log_divergence)
    if np.count_nonzero(valid) < 2:
        raise ValueError("Not enough valid divergence samples to estimate lambda.")

    # Skip the first point if possible to avoid the fixed initial condition.
    fit_mask = valid.copy()
    fit_mask[0] = False
    if np.count_nonzero(fit_mask) < 2:
        fit_mask = valid

    slope, intercept = np.polyfit(t_grid_s[fit_mask], mean_log_divergence[fit_mask], 1)
    logger.debug("Lyapunov slope={}, intercept={}", slope, intercept)
    return float(slope), mean_log_divergence


def predictability_horizon(lambda_s_inv: float, delta_max: float, delta_x0: float) -> float:
    """Compute the predictability horizon ``t*``.

    Raises
    ------
    ValueError
        If ``lambda_s_inv <= 0`` or the scale arguments are invalid.
    """

    if lambda_s_inv <= 0:
        raise ValueError("lambda_s_inv must be positive.")
    if delta_max <= 0 or delta_x0 <= 0:
        raise ValueError("delta_max and delta_x0 must be positive.")
    if delta_max <= delta_x0:
        raise ValueError("delta_max must exceed delta_x0.")

    horizon = (1.0 / lambda_s_inv) * np.log(delta_max / delta_x0)
    logger.debug("Predictability horizon={}", horizon)
    return float(horizon)
