"""Adapters turning precomputed forcing arrays into callables for the solvers.

``run_ensemble``/``run_deterministic`` call ``P0_t(t)``/``Q0_t(t)`` once per
step with a scalar time in seconds. ``soc_flare_forcing`` and
``lorenz63_precip_forcing`` instead return the whole forcing precomputed on
``t_grid_s``. This module bridges the two via linear interpolation.
"""

from __future__ import annotations

import numpy as np
from loguru import logger


def array_to_callable(t_grid_s: np.ndarray, values: np.ndarray):
    """Wrap a precomputed forcing array as a callable ``f(t)``."""

    t_grid_s = np.asarray(t_grid_s, dtype=float)
    values = np.asarray(values, dtype=float)
    if t_grid_s.shape != values.shape:
        raise ValueError("t_grid_s and values must have the same shape.")
    logger.debug("Wrapping array of {} samples as an interpolating callable", values.size)

    def _interp(t: float) -> float:
        return float(np.interp(t, t_grid_s, values))

    return _interp