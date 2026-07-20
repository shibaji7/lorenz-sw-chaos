"""Figure 2 ensemble comparison entry point."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from .._logging import configure_logging
from ..lyapunov import estimate_lyapunov, estimate_lyapunov_paired, predictability_horizon
from ..model_params import load_model_params
from ..plotting import format_axes, set_publication_style
from ..scenarios import build_chaotic_scenario
from ._save_utils import save_figure_pair


logger.debug("Loaded fig2 module")


def _safe_positive(values: np.ndarray, floor: float = 1.0e-6) -> np.ndarray:
    values = np.nan_to_num(values, nan=floor, posinf=floor, neginf=floor)
    return np.clip(values, floor, None)


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating SDE ensemble figure at {}", output_path)
    set_publication_style("nature")
    if params is None:
        params = load_model_params()

    scenario = build_chaotic_scenario(params)
    h_km, t_grid_s = scenario.h_km, scenario.t_grid_s
    deterministic, ensemble, n0 = scenario.deterministic, scenario.ensemble, scenario.n0

    final = _safe_positive(ensemble[:, -1, :])
    mean_final = _safe_positive(final.mean(axis=0))
    lo = _safe_positive(np.percentile(final, 10, axis=0))
    hi = _safe_positive(np.percentile(final, 90, axis=0))
    alt_index = int(np.argmin(np.abs(h_km - params["time_panel_altitude_km"])))
    time_lo = _safe_positive(np.percentile(ensemble[:, :, alt_index], 10, axis=0))
    time_hi = _safe_positive(np.percentile(ensemble[:, :, alt_index], 90, axis=0))

    lam_s_inv, _log_divergence = estimate_lyapunov(ensemble, t_grid_s, h_index=alt_index)
    tstar_hr = None
    if lam_s_inv > 0:
        delta_x0 = params["predictability_delta_x0_frac"] * n0[alt_index]
        delta_max = params["predictability_delta_max_frac"] * n0[alt_index]
        tstar_hr = predictability_horizon(lam_s_inv, delta_max, delta_x0) / 3600.0
        logger.info("Estimated lambda={:.3e} s^-1, t*={:.2f} h", lam_s_inv, tstar_hr)
    else:
        logger.warning(
            "Non-positive Lyapunov estimate (lambda={:.3e} s^-1); t* not annotated.", lam_s_inv,
        )

    # Twin-experiment cross-check: isolates the deterministic dynamics' sensitivity
    # to initial conditions (identical chaotic forcing, no stochastic diffusion),
    # rather than SDE ensemble-spread growth from independent noise realizations.
    lam_paired_s_inv, _sep_paired = estimate_lyapunov_paired(
        n0=n0, t_grid_s=t_grid_s, h_km=h_km,
        P0_t=scenario.P0_t, Q0_t=scenario.Q0_t, precip_model=scenario.precip_model,
        h_m_km=params["h_m_km"], H_km=params["H_km"], chi_rad=0.0,
        alpha_cm3s=params["alpha_cm3s"], beta_s=params["beta_s"],
        h_index=alt_index,
    )
    tstar_paired_hr = None
    if lam_paired_s_inv > 0:
        delta_x0 = params["predictability_delta_x0_frac"] * n0[alt_index]
        delta_max = params["predictability_delta_max_frac"] * n0[alt_index]
        tstar_paired_hr = predictability_horizon(lam_paired_s_inv, delta_max, delta_x0) / 3600.0
        logger.info("Paired-IC lambda={:.3e} s^-1, t*_IC={:.2f} h", lam_paired_s_inv, tstar_paired_hr)
    else:
        logger.warning("Non-positive paired-IC Lyapunov estimate (lambda={:.3e} s^-1).", lam_paired_s_inv)

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
    if tstar_hr is not None and 0.0 <= tstar_hr <= times_hr[-1]:
        ax.axvline(tstar_hr, color="black", linewidth=1.1, linestyle="-.", label=rf"$t^*$ = {tstar_hr:.1f} h")
    if tstar_paired_hr is not None and 0.0 <= tstar_paired_hr <= times_hr[-1]:
        ax.axvline(tstar_paired_hr, color="0.4", linewidth=1.1, linestyle=":", label=rf"$t^*_{{IC}}$ = {tstar_paired_hr:.1f} h")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel(r"$n$ at 90 km [cm$^{-3}$]")
    ax.set_title(rf"90 km response ($\lambda_{{ens}}$={lam_s_inv:.2e}, $\lambda_{{IC}}$={lam_paired_s_inv:.2e} s$^{{-1}}$)")
    ax.legend(frameon=False, fontsize=8)
    format_axes(ax)

    fig.suptitle("SDE ensemble versus deterministic solution (SOC + Lorenz-63 forcing)", y=1.03)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_figure_pair(fig, output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path
