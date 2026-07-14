"""Shared scenario builder for the chaotic-forcing figures (Fig. 2 and Fig. 3).

Both figures need the *same* physical realization of the chaotic SOC + Lorenz-63
forcing evolved through the continuity-equation solver: Fig. 2 shows the
ensemble/deterministic response directly, Fig. 3 decomposes that same
deterministic trajectory with DMD. Factoring the run out avoids the two
figures silently drifting apart (which is what happened with the previous
implementation, where Fig. 3 plotted a synthetic sinusoid unrelated to the
model at all).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from loguru import logger

from .chapman import chapman_production
from .ensemble import run_deterministic, run_ensemble
from .forcing.adapters import array_to_callable
from .forcing.lorenz_precip import lorenz63_precip_forcing
from .forcing.soc_flare import soc_flare_forcing
from .precipitation import gaussian_precipitation


logger.debug("Loaded scenarios module")


@dataclass
class ChaoticScenario:
    t_grid_s: np.ndarray
    h_km: np.ndarray
    n0: np.ndarray
    deterministic: np.ndarray
    ensemble: np.ndarray
    P0_t: object
    Q0_t: object
    precip_model: object


@dataclass
class ChaoticForcing:
    """Just the forcing/IC pieces, without running the (slow) full ensemble.

    ``build_chaotic_scenario`` always runs both ``run_deterministic`` and the
    80-member ``run_ensemble`` internally, which dominates its cost (tens of
    seconds, from nested Python loops over small altitude arrays). Callers
    that only need the forcing callables and initial profile -- e.g. a twin-
    experiment Lyapunov diagnostic, which calls ``run_deterministic`` on its
    own -- should use ``build_chaotic_forcing`` instead to avoid paying for
    an ensemble run they never use.
    """

    t_grid_s: np.ndarray
    h_km: np.ndarray
    n0: np.ndarray
    P0_t: object
    Q0_t: object
    precip_model: object


def _initial_density_profile(h_km: np.ndarray, P0_t, params: dict) -> np.ndarray:
    baseline = chapman_production(
        h_km, 0.0, P0_t,
        h_m_km=params["initial_chapman_h_m_km"],
        H_km=params["initial_chapman_H_km"],
        chi_rad=params["initial_chi_rad"],
    )
    baseline = baseline / np.max(baseline)
    return (
        params["initial_profile_floor_cm3"]
        + params["initial_profile_scale_cm3"] * baseline ** params["initial_profile_exponent"]
    )


def build_chaotic_forcing(params: dict) -> ChaoticForcing:
    """Build the SOC + Lorenz-63 forcing callables and initial profile only.

    Fast (sub-second): no ``run_deterministic``/``run_ensemble`` calls.
    """

    h_km = np.linspace(params["h_km_min"], params["h_km_max"], int(params["h_km_points"]))
    t_grid_s = np.arange(0.0, params["t_end_s"] + params["t_step_s"], params["t_step_s"])

    P0_arr = soc_flare_forcing(
        t_grid_s,
        rate_per_day=params["soc_rate_per_day"],
        alpha_powerlaw=params["soc_alpha_powerlaw"],
        P0_background=params["P0_amp"],
        P0_peak_scale=params["soc_P0_peak_scale"],
        seed=int(params["seed"]),
    )
    Q0_arr = lorenz63_precip_forcing(
        t_grid_s,
        sigma=params["lorenz_sigma"],
        rho=params["lorenz_rho"],
        beta=params["lorenz_beta"],
        Q_mean_eV=params["Q0_amp"],
        kappa=params["lorenz_kappa"],
        seed=int(params["seed"]) + 1,
        chaos_rate_s_inv=params["lorenz_chaos_rate_s_inv"],
    )
    P0_t = array_to_callable(t_grid_s, P0_arr)
    Q0_t = array_to_callable(t_grid_s, Q0_arr)

    precip_h_p_km = params["h_m_km"] + params["precip_peak_offset_km"]
    precip_model = lambda h, t: gaussian_precipitation(
        h, t, Q0_t=Q0_t, h_p_km=precip_h_p_km, H_p_km=params["precip_H_p_km"],
    )

    n0 = _initial_density_profile(h_km, P0_t, params)

    return ChaoticForcing(
        t_grid_s=t_grid_s, h_km=h_km, n0=n0, P0_t=P0_t, Q0_t=Q0_t, precip_model=precip_model,
    )


def build_chaotic_scenario(params: dict) -> ChaoticScenario:
    """Build the SOC (photoionization) + Lorenz-63 (precipitation) forced run,
    including the full deterministic trajectory and stochastic ensemble.

    This is the expensive path (the ``n_members``-member ``run_ensemble`` call
    dominates, tens of seconds for typical ``model_params.json`` settings).
    Use ``build_chaotic_forcing`` instead if you only need the forcing
    callables and initial profile.
    """

    forcing = build_chaotic_forcing(params)
    t_grid_s, h_km, n0 = forcing.t_grid_s, forcing.h_km, forcing.n0
    P0_t, Q0_t, precip_model = forcing.P0_t, forcing.Q0_t, forcing.precip_model

    logger.info(
        "Building chaotic scenario: t_end={:.1f} h, dt={:.0f} s",
        params["t_end_s"] / 3600.0, params["t_step_s"],
    )

    deterministic = run_deterministic(
        n0=n0, t_grid_s=t_grid_s, h_km=h_km, P0_t=P0_t, Q0_t=Q0_t,
        precip_model=precip_model, h_m_km=params["h_m_km"], H_km=params["H_km"],
        chi_rad=0.0, alpha_cm3s=params["alpha_cm3s"], beta_s=params["beta_s"],
    )
    ensemble = run_ensemble(
        n0=n0, t_grid_s=t_grid_s, h_km=h_km, P0_t=P0_t, Q0_t=Q0_t,
        precip_model=precip_model, h_m_km=params["h_m_km"], H_km=params["H_km"],
        chi_rad=0.0, alpha_cm3s=params["alpha_cm3s"], beta_s=params["beta_s"],
        sigma0=params["sigma0"], beta_g=params["beta_g"], P_max=params["P_max"],
        n_members=int(params["n_members"]), seed=int(params["seed"]),
    )

    return ChaoticScenario(
        t_grid_s=t_grid_s, h_km=h_km, n0=n0, deterministic=deterministic, ensemble=ensemble,
        P0_t=P0_t, Q0_t=Q0_t, precip_model=precip_model,
    )
