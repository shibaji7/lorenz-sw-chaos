"""Figure 2 ensemble comparison entry point."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from ..chapman import chapman_production
from ..ensemble import run_deterministic, run_ensemble
from ..plotting import format_axes, set_publication_style
from ..precipitation import gaussian_precipitation
from .._logging import configure_logging
from ..model_params import load_model_params


logger.debug("Loaded fig2 module")


def _safe_positive(values: np.ndarray, floor: float = 1.0e-6) -> np.ndarray:
    values = np.nan_to_num(values, nan=floor, posinf=floor, neginf=floor)
    return np.clip(values, floor, None)


def _initial_density_profile(h_km: np.ndarray, P0_t, params: dict[str, float]) -> np.ndarray:
    """Build a smooth Chapman-shaped starting profile for the ensemble."""

    baseline = chapman_production(
        h_km,
        0.0,
        P0_t,
        h_m_km=params["initial_chapman_h_m_km"],
        H_km=params["initial_chapman_H_km"],
        chi_rad=params["initial_chi_rad"],
    )
    baseline = baseline / np.max(baseline)
    return params["initial_profile_floor_cm3"] + params["initial_profile_scale_cm3"] * baseline**params["initial_profile_exponent"]


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating SDE ensemble figure at {}", output_path)
    set_publication_style("nature")
    if params is None:
        params = load_model_params()
    h_km = np.linspace(params["h_km_min"], params["h_km_max"], int(params["h_km_points"]))
    t_grid_s = np.arange(0.0, params["t_end_s"] + params["t_step_s"], params["t_step_s"])

    P0_t = lambda t: params["P0_amp"] * (
        1.0 + params["P0_modulation"] * np.sin(2.0 * np.pi * t / params["P0_period_s"])
    )
    Q0_t = lambda t: params["Q0_amp"] * (
        1.0 + params["Q0_modulation"] * np.cos(2.0 * np.pi * t / params["Q0_period_s"])
    )
    precip_model = lambda h, t: gaussian_precipitation(
        h,
        t,
        Q0_t=lambda tau: params["Q0_amp"]
        * (1.0 + params["Q0_modulation"] * np.cos(2.0 * np.pi * tau / params["Q0_period_s"])),
        h_p_km=lambda tau: params["h_m_km"]
        + params["precip_peak_offset_km"] * np.sin(2.0 * np.pi * tau / params["Q0_period_s"]),
        H_p_km=params["precip_H_p_km"],
    )
    n0 = _initial_density_profile(h_km, P0_t, params)

    deterministic = run_deterministic(
        n0=n0,
        t_grid_s=t_grid_s,
        h_km=h_km,
        P0_t=P0_t,
        Q0_t=Q0_t,
        precip_model=precip_model,
        h_m_km=params["h_m_km"],
        H_km=params["H_km"],
        chi_rad=0.0,
        alpha_cm3s=params["alpha_cm3s"],
        beta_s=params["beta_s"],
    )
    ensemble = run_ensemble(
        n0=n0,
        t_grid_s=t_grid_s,
        h_km=h_km,
        P0_t=P0_t,
        Q0_t=Q0_t,
        precip_model=precip_model,
        h_m_km=params["h_m_km"],
        H_km=params["H_km"],
        chi_rad=0.0,
        alpha_cm3s=params["alpha_cm3s"],
        beta_s=params["beta_s"],
        sigma0=params["sigma0"],
        beta_g=params["beta_g"],
        P_max=params["P_max"],
        n_members=int(params["n_members"]),
        seed=int(params["seed"]),
    )

    final = _safe_positive(ensemble[:, -1, :])
    mean_final = _safe_positive(final.mean(axis=0))
    lo = _safe_positive(np.percentile(final, 10, axis=0))
    hi = _safe_positive(np.percentile(final, 90, axis=0))
    alt_index = int(np.argmin(np.abs(h_km - params["time_panel_altitude_km"])))
    time_lo = _safe_positive(np.percentile(ensemble[:, :, alt_index], 10, axis=0))
    time_hi = _safe_positive(np.percentile(ensemble[:, :, alt_index], 90, axis=0))

    fig, axes = plt.subplots(1, 2, figsize=(params["figure_width_in"], params["figure_height_in"]))
    ax = axes[0]
    ax.fill_betweenx(h_km, lo, hi, color="tab:blue", alpha=0.18, label="10-90% ensemble")
    ax.plot(mean_final, h_km, color="tab:blue", linewidth=2.4, label="ensemble mean")
    ax.plot(deterministic[-1], h_km, color="tab:red", linewidth=2.0, linestyle="--", label="deterministic")
    ax.plot(n0, h_km, color="0.25", linewidth=1.6, linestyle=":", label="initial profile")
    ax.set_xscale("log")
    ax.set_xlim(params["xlim_min_cm3"], params["xlim_max_cm3"])
    ax.set_xlabel(r"Electron density $n$ [cm$^{-3}$]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Final-time density profile")
    ax.legend(frameon=False, fontsize=8)
    format_axes(ax)

    ax = axes[1]
    times_hr = t_grid_s / 3600.0
    ax.fill_between(times_hr, time_lo, time_hi, color="tab:blue", alpha=0.16, label="10-90% ensemble")
    ax.plot(times_hr, _safe_positive(ensemble[:, :, alt_index].mean(axis=0)), color="tab:blue", linewidth=2.2, label="ensemble mean")
    ax.plot(times_hr, _safe_positive(deterministic[:, alt_index]), color="tab:red", linewidth=2.0, linestyle="--", label="deterministic")
    ax.axhline(float(n0[alt_index]), color="0.25", linewidth=1.2, linestyle=":", label="initial")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel(r"$n$ at 90 km [cm$^{-3}$]")
    ax.set_title("90 km response with uncertainty")
    ax.legend(frameon=False, fontsize=8)
    format_axes(ax)

    fig.suptitle("SDE ensemble versus deterministic solution", y=1.03)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path
