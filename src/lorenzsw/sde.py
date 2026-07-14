"""Stochastic differential equation helpers."""

from __future__ import annotations

import numpy as np
from loguru import logger


logger.debug("Loaded sde module")


def diffusion_term(
    n: np.ndarray,
    P_precip: np.ndarray,
    P_max: float,
    sigma0: float,
    beta_g: float,
) -> np.ndarray:
    """Diffusion amplitude ``g(n,t)``.

    The form follows the handoff specification:
    ``sigma0 * (1 + beta_g * P_precip / P_max) * sqrt(n)``.
    """

    n = np.asarray(n, dtype=float)
    P_precip = np.asarray(P_precip, dtype=float)
    if P_max <= 0:
        raise ValueError("P_max must be positive.")
    if sigma0 < 0:
        raise ValueError("sigma0 must be non-negative.")
    if beta_g < 0:
        raise ValueError("beta_g must be non-negative.")

    scale = 1.0 + beta_g * np.clip(P_precip / P_max, a_min=0.0, a_max=None)
    return sigma0 * scale * np.sqrt(np.clip(n, a_min=0.0, a_max=None))


def euler_maruyama_step(
    n: np.ndarray,
    drift: np.ndarray,
    diffusion: np.ndarray,
    dt_s: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Advance one Euler-Maruyama step with a reflecting boundary.

    Negative values are reflected to preserve non-negativity instead of being
    clipped silently.
    """

    n = np.asarray(n, dtype=float)
    drift = np.asarray(drift, dtype=float)
    diffusion = np.asarray(diffusion, dtype=float)
    if dt_s <= 0:
        raise ValueError("dt_s must be positive.")

    dW = rng.normal(loc=0.0, scale=np.sqrt(dt_s), size=n.shape)
    n_next = n + drift * dt_s + diffusion * dW
    return np.abs(n_next)


def imex_step(
    n: np.ndarray,
    P_total: np.ndarray,
    alpha_cm3s: float,
    beta_s: float,
    diffusion: np.ndarray,
    dt_s: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Semi-implicit (IMEX) Euler-Maruyama step.

    Production and stochastic diffusion are treated explicitly; the quadratic
    (``alpha_cm3s * n**2``) and linear (``beta_s * n``) loss terms are treated
    implicitly. This is unconditionally stable in the loss term regardless of
    ``dt_s`` or pulse amplitude, unlike ``euler_maruyama_step``, which was
    observed to overflow to ~1e269 within the first two steps once an early SOC
    pulse pushed ``alpha_cm3s * n * dt_s`` past the explicit stability margin.
    """

    n = np.asarray(n, dtype=float)
    P_total = np.asarray(P_total, dtype=float)
    diffusion = np.asarray(diffusion, dtype=float)
    if dt_s <= 0:
        raise ValueError("dt_s must be positive.")

    n_deterministic = (n + P_total * dt_s) / (1.0 + alpha_cm3s * n * dt_s + beta_s * dt_s)
    dW = rng.normal(loc=0.0, scale=np.sqrt(dt_s), size=n.shape)
    return np.abs(n_deterministic + diffusion * dW)
