"""Lyapunov and predictability utilities."""

from __future__ import annotations

import numpy as np
from loguru import logger

from .ensemble import run_deterministic


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


def estimate_lyapunov_paired(
    n0: np.ndarray,
    t_grid_s: np.ndarray,
    h_km: np.ndarray,
    P0_t,
    Q0_t,
    precip_model,
    h_m_km: float,
    H_km: float,
    chi_rad: float,
    alpha_cm3s: float,
    beta_s: float,
    h_index: int = 0,
    epsilon_frac: float = 1.0e-4,
    fit_frac: float = 0.25,
) -> tuple[float, np.ndarray]:
    """Twin-experiment (paired-perturbed-IC) Lyapunov estimate.

    Unlike ``estimate_lyapunov``, which measures how fast independent noise
    realizations decorrelate ensemble members started from the *same*
    initial condition (SDE diffusion spreading), this isolates the
    deterministic dynamics' sensitivity to initial conditions: two
    noise-free trajectories with nearly identical ``n0`` (differing by
    ``epsilon_frac`` at ``h_index``), driven by *identical* chaotic forcing.
    Any divergence is attributable purely to the nonlinear continuity
    equation's response to a small IC perturbation.

    The slope is fit only over the first ``fit_frac`` of the time grid,
    since separation grows exponentially only until it saturates near the
    system's natural variability scale; fitting the full window would bias
    the estimate low once saturation sets in.

    Caveat (see estimate_lyapunov_renormalized): if the true contraction or
    growth rate is fast relative to the window, separation can underflow to
    floating-point noise within the first few steps, in which case this
    fitted slope reflects "time to underflow" rather than a resolved rate.
    """

    n0 = np.asarray(n0, dtype=float)
    t_grid_s = np.asarray(t_grid_s, dtype=float)
    if not (0 <= h_index < n0.size):
        raise ValueError("h_index is out of range.")
    if epsilon_frac <= 0:
        raise ValueError("epsilon_frac must be positive.")
    if not (0.0 < fit_frac <= 1.0):
        raise ValueError("fit_frac must be in (0, 1].")
    if t_grid_s.size < 2:
        raise ValueError("t_grid_s must contain at least two points.")

    n0_base = n0.copy()
    n0_pert = n0.copy()
    n0_pert[h_index] *= (1.0 + epsilon_frac)

    kwargs = dict(
        t_grid_s=t_grid_s, h_km=h_km, P0_t=P0_t, Q0_t=Q0_t,
        precip_model=precip_model, h_m_km=h_m_km, H_km=H_km,
        chi_rad=chi_rad, alpha_cm3s=alpha_cm3s, beta_s=beta_s,
    )
    traj_base = run_deterministic(n0=n0_base, **kwargs)
    traj_pert = run_deterministic(n0=n0_pert, **kwargs)

    separation = np.abs(traj_pert[:, h_index] - traj_base[:, h_index])
    log_sep = np.log(np.clip(separation, 1e-300, None))

    n_fit = max(2, int(fit_frac * t_grid_s.size))
    slope, intercept = np.polyfit(t_grid_s[:n_fit], log_sep[:n_fit], 1)
    logger.debug(
        "Paired-IC Lyapunov slope={} (fit over first {} of {} points)",
        slope, n_fit, t_grid_s.size,
    )
    return float(slope), separation


def estimate_lyapunov_renormalized(
    n0: np.ndarray,
    t_grid_s: np.ndarray,
    h_km: np.ndarray,
    P0_t,
    Q0_t,
    precip_model,
    h_m_km: float,
    H_km: float,
    chi_rad: float,
    alpha_cm3s: float,
    beta_s: float,
    h_index: int = 0,
    epsilon_frac: float = 1.0e-4,
    renorm_every: int = 1,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Renormalized (Benettin/Wolf-style) twin-experiment Lyapunov estimate.

    estimate_lyapunov_paired tracks one fixed initial perturbation over the
    whole window and fits a single slope; if the true contraction (or
    growth) rate is fast, the separation underflows to floating-point noise
    within the first few steps, and the rest of the window contributes no
    real signal to the fit -- the reported slope then reflects "time to
    underflow", not a resolved rate. This function avoids that by rescaling
    the perturbed trajectory back to epsilon_frac-sized separation every
    renorm_every steps, accumulating the log of each interval's growth
    factor. The Benettin estimate is the time-average of these log-factors,
    and is well-defined regardless of how fast local contraction/expansion is.

    Because the continuity equation has no vertical coupling (each altitude's
    ODE is independent of the others), this runs on a single altitude only.

    Returns (lambda_s_inv, times_at_renorm_s, log_growth_factors) where the
    latter is a per-interval *local* rate estimate (in log-growth-per-
    interval, not yet normalized by dt) -- useful for checking whether
    contraction weakens or reverses during forcing pulses.
    """

    n0 = np.asarray(n0, dtype=float)
    t_grid_s = np.asarray(t_grid_s, dtype=float)
    if not (0 <= h_index < n0.size):
        raise ValueError("h_index is out of range.")
    if epsilon_frac <= 0:
        raise ValueError("epsilon_frac must be positive.")
    if renorm_every < 1:
        raise ValueError("renorm_every must be at least 1.")
    if t_grid_s.size < 2:
        raise ValueError("t_grid_s must contain at least two points.")

    h_scalar = np.array([h_km[h_index]], dtype=float)
    d0 = epsilon_frac * n0[h_index]
    if d0 <= 0:
        raise ValueError("epsilon_frac * n0[h_index] must be positive.")

    n_base = np.array([n0[h_index]], dtype=float)
    n_pert = np.array([n0[h_index] + d0], dtype=float)

    kwargs = dict(
        h_km=h_scalar, P0_t=P0_t, Q0_t=Q0_t, precip_model=precip_model,
        h_m_km=h_m_km, H_km=H_km, chi_rad=chi_rad,
        alpha_cm3s=alpha_cm3s, beta_s=beta_s,
    )

    log_growth = []
    times_at_renorm = []
    n_steps = t_grid_s.size - 1
    idx = 0
    while idx < n_steps:
        chunk_end = min(idx + renorm_every, n_steps)
        t_chunk = t_grid_s[idx:chunk_end + 1]

        traj_base = run_deterministic(n0=n_base, t_grid_s=t_chunk, **kwargs)
        traj_pert = run_deterministic(n0=n_pert, t_grid_s=t_chunk, **kwargs)

        n_base = traj_base[-1]
        n_pert_raw = traj_pert[-1]
        diff = float(n_pert_raw[0] - n_base[0])
        d_now = abs(diff)
        if d_now <= 0:
            d_now = np.finfo(float).tiny

        log_growth.append(np.log(d_now / d0))
        times_at_renorm.append(float(t_chunk[-1]))

        direction = 1.0 if diff >= 0 else -1.0
        n_pert = n_base + direction * d0

        idx = chunk_end

    log_growth = np.asarray(log_growth, dtype=float)
    times_at_renorm = np.asarray(times_at_renorm, dtype=float)
    total_time_s = times_at_renorm[-1] - t_grid_s[0]
    lambda_s_inv = float(np.sum(log_growth) / total_time_s)
    logger.debug(
        "Renormalized Lyapunov estimate: lambda={} s^-1 over {} intervals ({} s total)",
        lambda_s_inv, log_growth.size, total_time_s,
    )
    return lambda_s_inv, times_at_renorm, log_growth


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
