"""Figure 4 exceedance-probability entry point."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator
from loguru import logger

from .._logging import configure_logging
from ..ensemble import run_ensemble, run_gaussian_uq_ensemble
from ..forcing.adapters import array_to_callable
from ..forcing.soc_flare import soc_flare_forcing
from ..model_params import load_model_params
from ..precipitation import gaussian_precipitation
from ..plotting import format_axes, set_publication_style
from ._save_utils import save_figure_pair


logger.debug("Loaded fig4 module")


def _safe_positive(values: np.ndarray, floor: float = 1.0e-6) -> np.ndarray:
    values = np.nan_to_num(values, nan=floor, posinf=floor, neginf=floor)
    return np.clip(values, floor, None)


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating exceedance figure at {}", output_path)
    set_publication_style("nature")
    if params is None:
        params = load_model_params()
    h_km = np.linspace(params["fig4_h_km_min"], params["fig4_h_km_max"], int(params["fig4_h_km_points"]))
    t_grid_s = np.arange(0.0, params["fig4_t_end_s"] + params["fig4_t_step_s"], params["fig4_t_step_s"])
    n0 = np.full_like(h_km, params["fig4_n0_cm3"], dtype=float)

    P0_arr = soc_flare_forcing(
        t_grid_s,
        rate_per_day=params["soc_rate_per_day"],
        alpha_powerlaw=params["soc_alpha_powerlaw"],
        P0_background=params["fig4_P0_amp"],
        P0_peak_scale=params["soc_P0_peak_scale"],
        seed=int(params["fig4_seed"]),
    )
    P0_t = array_to_callable(t_grid_s, P0_arr)
    Q0_t = lambda t: params["fig4_Q0_amp"]
    precip_model = lambda h, t: gaussian_precipitation(
        h, t, Q0_t=Q0_t, h_p_km=params["fig4_precip_h_p_km"], H_p_km=params["fig4_precip_H_p_km"],
    )

    common_kwargs = dict(
        n0=n0, t_grid_s=t_grid_s, h_km=h_km, P0_t=P0_t, Q0_t=Q0_t,
        precip_model=precip_model, h_m_km=params["h_m_km"], H_km=params["H_km"],
        chi_rad=0.0, alpha_cm3s=params["fig4_alpha_cm3s"], beta_s=params["fig4_beta_s"],
    )
    ensemble = run_ensemble(
        **common_kwargs, sigma0=params["fig4_sigma0"], beta_g=params["fig4_beta_g"],
        P_max=params["fig4_P_max"], n_members=int(params["fig4_n_members"]), seed=int(params["fig4_seed"]),
    )
    gaussian_uq_ensemble = run_gaussian_uq_ensemble(
        **common_kwargs,
        n0_sigma_frac=params["gaussian_uq_n0_sigma_frac"],
        P0_sigma_frac=params["gaussian_uq_P0_sigma_frac"],
        n_members=int(params["fig4_n_members"]),
        seed=int(params["fig4_seed"]) + 100,
    )

    final = _safe_positive(ensemble[:, -1, :])
    final_gauss = _safe_positive(gaussian_uq_ensemble[:, -1, :])
    threshold_grid = np.linspace(np.percentile(final, 35), np.percentile(final, 97), 80)
    exceedance = np.array([(final > thr).mean(axis=0) for thr in threshold_grid])
    alt_index = int(np.argmin(np.abs(h_km - 90.0)))

    fig, axes = plt.subplots(1, 2, figsize=(params["fig4_figure_width_in"], params["fig4_figure_height_in"]))
    ax = axes[0]
    mesh = ax.contourf(
        threshold_grid, h_km, exceedance.T, levels=np.linspace(0.0, 1.0, 11), cmap="Blues", extend="neither",
    )
    ax.contour(
        threshold_grid, h_km, exceedance.T, levels=[0.25, 0.5, 0.75],
        colors=["#8c6d31", "#4d4d4d", "#08306b"], linewidths=[1.0, 1.4, 1.0],
    )
    ax.plot(np.median(final, axis=0), h_km, color="black", linewidth=1.8, label="median (SDE)")
    ax.set_xlabel(r"Threshold $n_\ast$ [cm$^{-3}$]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Final-time exceedance map (SDE)")
    ax.legend(frameon=False, fontsize=7, loc="lower left")
    format_axes(ax, grid=False)
    cbar = fig.colorbar(mesh, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label("Exceedance probability")

    ax = axes[1]
    for label, data, color in (
        ("SDE (multiplicative noise)", final[:, alt_index], "tab:red"),
        ("Gaussian UQ (IC/parameter perturbation)", final_gauss[:, alt_index], "tab:gray"),
    ):
        sorted_final = np.unique(np.sort(_safe_positive(data)))
        cdf = np.arange(1, sorted_final.size + 1) / sorted_final.size
        exceed = 1.0 - cdf
        ax.plot(sorted_final, exceed, linestyle="none", marker="o", markersize=2.6, color=color, alpha=0.4)
        if sorted_final.size >= 2:
            interp = PchipInterpolator(sorted_final, exceed, extrapolate=False)
            dense_x = np.linspace(sorted_final.min(), sorted_final.max(), 300)
            dense_y = np.clip(interp(dense_x), 0.0, 1.0)
        else:
            dense_x, dense_y = sorted_final, exceed
        ax.plot(dense_x, dense_y, color=color, linewidth=2.2, label=label)
    ax.set_xscale("log")
    ax.set_xlabel(r"$n$ at 90 km [cm$^{-3}$]")
    ax.set_ylabel("Exceedance probability")
    ax.set_title("Tail probability at 90 km: SDE vs. Gaussian UQ")
    ax.legend(frameon=False, fontsize=7, loc="lower left")
    format_axes(ax)

    fig.suptitle("Exceedance probabilities from the ensemble", y=1.03)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_figure_pair(fig, output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path
