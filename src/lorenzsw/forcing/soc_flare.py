"""SOC flare forcing proxy."""

from __future__ import annotations

import numpy as np
from loguru import logger


logger.debug("Loaded soc_flare forcing module")

_DEFAULT_DECAY_TIME_S = 1800.0


def _sample_powerlaw_amplitudes(
    rng: np.random.Generator,
    n_events: int,
    alpha_powerlaw: float,
    peak_scale: float,
) -> np.ndarray:
    """Sample positive pulse amplitudes with CCDF exponent ``alpha_powerlaw``."""

    if n_events < 0:
        raise ValueError("n_events must be non-negative.")
    if alpha_powerlaw <= 0:
        raise ValueError("alpha_powerlaw must be positive.")
    if peak_scale <= 0:
        raise ValueError("peak_scale must be positive.")
    if n_events == 0:
        return np.empty(0, dtype=float)

    u = np.clip(rng.random(n_events), np.finfo(float).tiny, 1.0)
    return peak_scale * u ** (-1.0 / alpha_powerlaw)


def _generate_soc_flare_events(
    t_grid_s: np.ndarray,
    rate_per_day: float,
    alpha_powerlaw: float,
    P0_peak_scale: float,
    seed: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate Poisson event times and power-law amplitudes for SOC flares."""

    t_grid_s = np.asarray(t_grid_s, dtype=float)
    if t_grid_s.ndim != 1 or t_grid_s.size < 1:
        raise ValueError("t_grid_s must be a one-dimensional array with at least one point.")
    if rate_per_day < 0:
        raise ValueError("rate_per_day must be non-negative.")
    if np.any(np.diff(t_grid_s) <= 0):
        raise ValueError("t_grid_s must be strictly increasing.")

    duration_s = float(t_grid_s[-1] - t_grid_s[0])
    if duration_s < 0:
        raise ValueError("t_grid_s must be increasing.")

    rng = np.random.default_rng(seed)
    rate_per_s = rate_per_day / 86400.0
    n_expected = rate_per_s * duration_s
    n_events = rng.poisson(n_expected)
    if n_events == 0:
        return np.empty(0, dtype=float), np.empty(0, dtype=float)

    interarrival = rng.exponential(scale=1.0 / rate_per_s, size=n_events)
    event_times = t_grid_s[0] + np.cumsum(interarrival)
    event_times = event_times[event_times <= t_grid_s[-1]]
    amplitudes = _sample_powerlaw_amplitudes(
        rng,
        event_times.size,
        alpha_powerlaw=alpha_powerlaw,
        peak_scale=P0_peak_scale,
    )
    logger.debug("Generated {} SOC flare events", event_times.size)
    return event_times, amplitudes


def soc_flare_forcing(
    t_grid_s: np.ndarray,
    rate_per_day: float,
    alpha_powerlaw: float,
    P0_background: float,
    P0_peak_scale: float,
    seed: int = 0,
) -> np.ndarray:
    """Synthetic photoionization peak forcing with SOC-like pulse statistics."""

    t_grid_s = np.asarray(t_grid_s, dtype=float)
    if t_grid_s.ndim != 1 or t_grid_s.size < 1:
        raise ValueError("t_grid_s must be a one-dimensional array with at least one point.")
    if P0_background < 0:
        raise ValueError("P0_background must be non-negative.")
    if np.any(np.diff(t_grid_s) <= 0):
        raise ValueError("t_grid_s must be strictly increasing.")

    logger.info("Generating SOC flare forcing over {} time points", t_grid_s.size)
    event_times, amplitudes = _generate_soc_flare_events(
        t_grid_s,
        rate_per_day=rate_per_day,
        alpha_powerlaw=alpha_powerlaw,
        P0_peak_scale=P0_peak_scale,
        seed=seed,
    )

    P0 = np.full_like(t_grid_s, fill_value=P0_background, dtype=float)
    if event_times.size == 0:
        return P0

    dt = t_grid_s[:, None] - event_times[None, :]
    decay = np.exp(-np.clip(dt, a_min=0.0, a_max=None) / _DEFAULT_DECAY_TIME_S)
    pulse_sum = np.sum(amplitudes[None, :] * decay * (dt >= 0.0), axis=1)
    out = P0 + pulse_sum
    logger.debug("SOC forcing range: [{}, {}]", float(np.min(out)), float(np.max(out)))
    return out
