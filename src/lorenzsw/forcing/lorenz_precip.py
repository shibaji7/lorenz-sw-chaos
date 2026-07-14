"""Lorenz-63 precipitation forcing proxy."""

from __future__ import annotations

import numpy as np
from loguru import logger
from scipy.integrate import solve_ivp


logger.debug("Loaded lorenz_precip forcing module")


def _lorenz63_rhs(t: float, state: np.ndarray, sigma: float, rho: float, beta: float) -> np.ndarray:
    x, y, z = state
    return np.array(
        [
            sigma * (y - x),
            x * (rho - z) - y,
            x * y - beta * z,
        ],
        dtype=float,
    )


def lorenz63_precip_forcing(
    t_grid_s: np.ndarray,
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8 / 3,
    Q_mean_eV: float = 1.0e3,
    kappa: float = 0.5,
    seed: int = 0,
    chaos_rate_s_inv: float = 1.0,
) -> np.ndarray:
    """Chaotic precipitation proxy derived from the Lorenz-63 system.

    ``chaos_rate_s_inv`` maps real elapsed seconds onto the Lorenz-63 system's
    own dimensionless time units (``tau = t_grid_s * chaos_rate_s_inv``). The
    default of 1.0 preserves the original behavior (one real second equals one
    Lorenz time unit) for backward compatibility. That default becomes
    impractical for windows longer than ~1-2 hours: Lorenz-63's natural
    oscillation period is O(1) time unit, so a 24-hour window at the default
    rate asks ``solve_ivp`` to resolve ~86,400 chaotic oscillation cycles at
    tight tolerance, which takes minutes. Callers integrating over
    hours-to-days of real time should pass an explicit ``chaos_rate_s_inv``
    (e.g. via ``model_params.json``) chosen so the mapped Lorenz-time window
    spans a modest, fast-to-integrate number of natural cycles (tens to a
    few hundred units) while still sampling multiple Lyapunov times of mixing.
    """

    t_grid_s = np.asarray(t_grid_s, dtype=float)
    if t_grid_s.ndim != 1 or t_grid_s.size < 1:
        raise ValueError("t_grid_s must be a one-dimensional array with at least one point.")
    if np.any(np.diff(t_grid_s) <= 0):
        raise ValueError("t_grid_s must be strictly increasing.")
    if Q_mean_eV <= 0:
        raise ValueError("Q_mean_eV must be positive.")
    if kappa < 0:
        raise ValueError("kappa must be non-negative.")
    if chaos_rate_s_inv <= 0:
        raise ValueError("chaos_rate_s_inv must be positive.")

    logger.info("Generating Lorenz-63 precipitation forcing over {} time points", t_grid_s.size)
    tau_grid = t_grid_s * chaos_rate_s_inv
    rng = np.random.default_rng(seed)
    y0 = np.array([1.0, 1.0, 1.0], dtype=float) + 0.01 * rng.standard_normal(3)
    sol = solve_ivp(
        _lorenz63_rhs,
        (float(tau_grid[0]), float(tau_grid[-1])),
        y0,
        t_eval=tau_grid,
        args=(sigma, rho, beta),
        rtol=1e-7,
        atol=1e-9,
        method="RK45",
    )
    if not sol.success:
        raise RuntimeError(f"Lorenz-63 integration failed: {sol.message}")

    x = sol.y[0]
    x_std = float(np.std(x))
    if x_std == 0:
        x_std = 1.0
    out = Q_mean_eV * (1.0 + kappa * x / x_std)
    out = np.maximum(0.0, out)
    logger.debug("Lorenz precipitation range: [{}, {}]", float(np.min(out)), float(np.max(out)))
    return out
