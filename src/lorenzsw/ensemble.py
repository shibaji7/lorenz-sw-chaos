"""Ensemble propagation utilities."""

from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from loguru import logger

from .chapman import chapman_production
from .sde import diffusion_term, euler_maruyama_step, imex_step
from .precipitation import PrecipitationModel


logger.debug("Loaded ensemble module")


def run_ensemble(
    n0: np.ndarray,
    t_grid_s: np.ndarray,
    h_km: np.ndarray,
    P0_t: Callable[[float], float],
    Q0_t: Callable[[float], float],
    precip_model: PrecipitationModel,
    h_m_km: float,
    H_km: float,
    chi_rad: float,
    alpha_cm3s: float,
    beta_s: float,
    sigma0: float,
    beta_g: float,
    P_max: float,
    n_members: int = 500,
    seed: int = 0,
) -> np.ndarray:
    """Propagate an ensemble using Euler-Maruyama."""

    n0 = np.asarray(n0, dtype=float)
    t_grid_s = np.asarray(t_grid_s, dtype=float)
    h_km = np.asarray(h_km, dtype=float)
    if t_grid_s.ndim != 1 or t_grid_s.size < 1:
        raise ValueError("t_grid_s must be a one-dimensional grid with at least one point.")
    if n_members < 1:
        raise ValueError("n_members must be at least 1.")
    if h_km.ndim != 1:
        raise ValueError("h_km must be one-dimensional.")
    if n0.shape != h_km.shape:
        raise ValueError("n0 and h_km must have the same shape.")

    logger.info("Running ensemble with {} members over {} time points", n_members, t_grid_s.size)
    rng = np.random.default_rng(seed)
    ensemble = np.empty((n_members, t_grid_s.size, h_km.size), dtype=float)

    for member in range(n_members):
        n = n0.copy()
        ensemble[member, 0] = n
        for k in range(t_grid_s.size - 1):
            t = float(t_grid_s[k])
            dt = float(t_grid_s[k + 1] - t_grid_s[k])
            if dt <= 0:
                raise ValueError("t_grid_s must be strictly increasing.")
            P_solar = chapman_production(h_km, t, P0_t, h_m_km, H_km, chi_rad)
            P_precip = precip_model(h_km, t)
            diffusion = diffusion_term(n, P_precip, P_max, sigma0, beta_g)
            n = imex_step(n, P_solar + P_precip, alpha_cm3s, beta_s, diffusion, dt, rng)
            ensemble[member, k + 1] = n

    return ensemble


def run_deterministic(
    n0: np.ndarray,
    t_grid_s: np.ndarray,
    h_km: np.ndarray,
    P0_t: Callable,
    Q0_t: Callable,
    precip_model: PrecipitationModel,
    h_m_km: float,
    H_km: float,
    chi_rad: float,
    alpha_cm3s: float,
    beta_s: float,
) -> np.ndarray:
    """Run a single noise-free trajectory."""

    n0 = np.asarray(n0, dtype=float)
    t_grid_s = np.asarray(t_grid_s, dtype=float)
    h_km = np.asarray(h_km, dtype=float)
    if t_grid_s.ndim != 1 or t_grid_s.size < 1:
        raise ValueError("t_grid_s must be a one-dimensional grid with at least one point.")
    if h_km.ndim != 1:
        raise ValueError("h_km must be one-dimensional.")
    if n0.shape != h_km.shape:
        raise ValueError("n0 and h_km must have the same shape.")

    logger.info("Running deterministic trajectory over {} time points", t_grid_s.size)
    n_hist = np.empty((t_grid_s.size, h_km.size), dtype=float)
    n = n0.copy()
    n_hist[0] = n
    for k in range(t_grid_s.size - 1):
        t = float(t_grid_s[k])
        dt = float(t_grid_s[k + 1] - t_grid_s[k])
        if dt <= 0:
            raise ValueError("t_grid_s must be strictly increasing.")
        P_solar = chapman_production(h_km, t, P0_t, h_m_km, H_km, chi_rad)
        P_precip = precip_model(h_km, t)
        n = np.abs((n + (P_solar + P_precip) * dt) / (1.0 + alpha_cm3s * n * dt + beta_s * dt))
        n_hist[k + 1] = n
    return n_hist


def run_gaussian_uq_ensemble(
    n0: np.ndarray,
    t_grid_s: np.ndarray,
    h_km: np.ndarray,
    P0_t: Callable[[float], float],
    Q0_t: Callable[[float], float],
    precip_model: PrecipitationModel,
    h_m_km: float,
    H_km: float,
    chi_rad: float,
    alpha_cm3s: float,
    beta_s: float,
    n0_sigma_frac: float = 0.05,
    P0_sigma_frac: float = 0.05,
    n_members: int = 500,
    seed: int = 0,
) -> np.ndarray:
    """Classical Gaussian-UQ ensemble: perturb IC/production, propagate deterministically.

    Distinct from ``run_ensemble``: no continuous multiplicative noise term. Each
    member draws one Gaussian-perturbed initial condition and one Gaussian
    production-scale factor, then evolves under the same drift as
    ``run_deterministic``. Intentionally ignores ``sigma0``/``beta_g``/``P_max``.
    """

    n0 = np.asarray(n0, dtype=float)
    if n_members < 1:
        raise ValueError("n_members must be at least 1.")

    logger.info("Running Gaussian-UQ ensemble with {} members", n_members)
    rng = np.random.default_rng(seed)
    ensemble = np.empty((n_members, t_grid_s.size, h_km.size), dtype=float)

    for member in range(n_members):
        n0_pert = np.abs(n0 * (1.0 + n0_sigma_frac * rng.standard_normal(n0.shape)))
        p0_scale = 1.0 + P0_sigma_frac * rng.standard_normal()
        P0_t_pert = (lambda t, _scale=p0_scale: _scale * P0_t(t))
        ensemble[member] = run_deterministic(
            n0=n0_pert,
            t_grid_s=t_grid_s,
            h_km=h_km,
            P0_t=P0_t_pert,
            Q0_t=Q0_t,
            precip_model=precip_model,
            h_m_km=h_m_km,
            H_km=H_km,
            chi_rad=chi_rad,
            alpha_cm3s=alpha_cm3s,
            beta_s=beta_s,
        )

    return ensemble


def calibrate_drift_diffusion(
    n_hist: np.ndarray,
    dt_s: float,
    n_bins: int = 30,
) -> tuple[Callable[[float], float], Callable[[float], float]]:
    """Estimate drift and diffusion from a 1D time series.

    Returns interpolating callables ``(f_hat, g_hat)`` based on conditional
    first and second moments in bins of ``n_hist``.
    """

    n_hist = np.asarray(n_hist, dtype=float).ravel()
    if n_hist.size < 3:
        raise ValueError("n_hist must contain at least three points.")
    if dt_s <= 0:
        raise ValueError("dt_s must be positive.")
    if n_bins < 2:
        raise ValueError("n_bins must be at least 2.")

    logger.info("Calibrating drift and diffusion from {} samples", n_hist.size)
    n_mid = n_hist[:-1]
    increments = np.diff(n_hist)
    bins = np.linspace(np.min(n_mid), np.max(n_mid), n_bins + 1)
    centers = 0.5 * (bins[:-1] + bins[1:])

    f_vals = np.zeros_like(centers)
    g_vals = np.zeros_like(centers)
    for i in range(centers.size):
        if i == centers.size - 1:
            mask = (n_mid >= bins[i]) & (n_mid <= bins[i + 1])
        else:
            mask = (n_mid >= bins[i]) & (n_mid < bins[i + 1])
        if np.any(mask):
            local_inc = increments[mask]
            f_vals[i] = np.mean(local_inc) / dt_s
            g_vals[i] = np.sqrt(max(np.mean(local_inc**2) / dt_s, 0.0))
        else:
            f_vals[i] = 0.0
            g_vals[i] = 0.0

    def f_hat(x: float) -> float:
        return float(np.interp(x, centers, f_vals, left=f_vals[0], right=f_vals[-1]))

    def g_hat(x: float) -> float:
        return float(np.interp(x, centers, g_vals, left=g_vals[0], right=g_vals[-1]))

    return f_hat, g_hat
