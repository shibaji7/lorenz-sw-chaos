"""Generate a visually distinct paper-claim figure set."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from loguru import logger

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("/tmp") / "xdg-cache"))
Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator

from lorenzsw._logging import configure_logging
from lorenzsw.chapman import chapman_production
from lorenzsw.ensemble import run_deterministic, run_ensemble
from lorenzsw.figures.fig1_swmi_schematic import make_figure as make_baseline_fig1
from lorenzsw.lyapunov import estimate_lyapunov, predictability_horizon
from lorenzsw.model_params import load_model_params
from lorenzsw.plotting import format_axes, set_publication_style
from lorenzsw.precipitation import gaussian_precipitation
from lorenzsw.transfer_operator import dmd_transfer_operator

from _source_term_plot_utils import mirror_figure_to_docs


def _claim_params(params: dict) -> dict:
    claim = dict(params)
    claim.update(
        {
            "claim_t_end_s": max(float(params["t_end_s"]) * 2.0, 14400.0),
            "claim_t_step_s": max(float(params["t_step_s"]), 60.0),
            "claim_sigma0": max(float(params["sigma0"]) * 0.8, 0.9),
            "claim_beta_g": max(float(params["beta_g"]) * 1.05, 3.4),
            "claim_P_max": max(float(params["P_max"]) * 0.85, 500.0),
            "claim_n_members": max(int(params["n_members"]), 72),
            "claim_seed": int(params["seed"]) + 77,
            "claim_fig3_rank": min(max(int(params["fig3_dmd_rank"]) + 4, 6), 12),
            "claim_fig4_sigma0": max(float(params["fig4_sigma0"]) * 4.0, 0.02),
            "claim_fig4_beta_g": max(float(params["fig4_beta_g"]) * 2.0, 0.8),
            "claim_fig4_P_max": max(float(params["fig4_P_max"]) * 0.7, 1000.0),
            "claim_fig4_n_members": max(int(params["fig4_n_members"]), 72),
            "claim_fig4_seed": int(params["fig4_seed"]) + 33,
            "claim_gauss_ic_sigma": max(float(params["fig4_n0_cm3"]) * 0.06, 350.0),
            "claim_gauss_param_sigma": 0.12,
        }
    )
    return claim


def _initial_density_profile(h_km: np.ndarray, P0_t, params: dict[str, float]) -> np.ndarray:
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


def _safe_positive(values: np.ndarray, floor: float = 1.0e-6) -> np.ndarray:
    values = np.nan_to_num(values, nan=floor, posinf=floor, neginf=floor)
    return np.clip(values, floor, None)


def _build_forcing(params: dict, prefix: str):
    P0_t = lambda t: params[f"{prefix}P0_amp"] * (
        1.0 + params[f"{prefix}P0_modulation"] * np.sin(2.0 * np.pi * t / params[f"{prefix}P0_period_s"])
    )
    Q0_t = lambda t: params[f"{prefix}Q0_amp"] * (
        1.0 + params[f"{prefix}Q0_modulation"] * np.cos(2.0 * np.pi * t / params[f"{prefix}Q0_period_s"])
    )
    precip_model = lambda h, t: gaussian_precipitation(
        h,
        t,
        Q0_t=Q0_t,
        h_p_km=lambda tau: params["h_m_km"]
        + params[f"{prefix}precip_peak_offset_km"] * np.sin(2.0 * np.pi * tau / params[f"{prefix}Q0_period_s"]),
        H_p_km=params[f"{prefix}precip_H_p_km"],
    )
    return P0_t, Q0_t, precip_model


def _fig1_claim(output_path: Path, params: dict) -> Path:
    logger.info("Creating claim schematic at {}", output_path)
    fig, ax = plt.subplots(figsize=(7.4, 4.3))
    ax.set_axis_off()
    ax.set_facecolor("#fbfbf8")

    boxes = {
        "Sun / forcing": (0.06, 0.64, 0.18, 0.16, "#d98e3a"),
        "Chaotic source\nmodulation": (0.32, 0.68, 0.22, 0.16, "#4c72b0"),
        "Ionosphere\n$n(h,t)$": (0.60, 0.58, 0.18, 0.24, "#25476a"),
        "Observables": (0.82, 0.64, 0.13, 0.14, "#b85c38"),
    }
    for label, (x, y, w, h, color) in boxes.items():
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="#202020", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color="white", fontsize=11)

    arrows = [
        ((0.24, 0.71), (0.32, 0.75), "photoionization"),
        ((0.54, 0.75), (0.60, 0.70), "stochastic continuity"),
        ((0.78, 0.70), (0.82, 0.71), "data comparison"),
        ((0.69, 0.58), (0.69, 0.36), "recombination + loss"),
        ((0.42, 0.58), (0.42, 0.36), "precipitation forcing"),
    ]
    for start, end, text in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", linewidth=1.8, color="#303030"))
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.03, text, ha="center", fontsize=8)

    ax.text(
        0.5,
        0.18,
        "Claim set: longer-window ensemble, explicit spread diagnostics, and threshold-tail views.",
        ha="center",
        fontsize=10.5,
        fontweight="semibold",
    )
    ax.add_patch(plt.Rectangle((0.03, 0.08), 0.94, 0.82, fill=False, linewidth=1.0, linestyle="--", edgecolor="0.55"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path


def _fig2_claim(output_path: Path, params: dict) -> tuple[Path, np.ndarray, np.ndarray]:
    logger.info("Creating claim ensemble figure at {}", output_path)
    set_publication_style("nature")
    h_km = np.linspace(params["h_km_min"], params["h_km_max"], int(params["h_km_points"]))
    t_grid_s = np.arange(0.0, params["claim_t_end_s"] + params["claim_t_step_s"], params["claim_t_step_s"])
    P0_t, Q0_t, precip_model = _build_forcing(params, prefix="")
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
        sigma0=params["claim_sigma0"],
        beta_g=params["claim_beta_g"],
        P_max=params["claim_P_max"],
        n_members=params["claim_n_members"],
        seed=params["claim_seed"],
    )
    ensemble = _safe_positive(np.nan_to_num(ensemble, nan=np.nanmedian(n0), posinf=np.nanmax(n0) * 20.0, neginf=1.0))

    alt_index = int(np.argmin(np.abs(h_km - params["forecast_altitude_km"])))
    lambda_hat, mean_log_div = estimate_lyapunov(ensemble, t_grid_s, h_index=alt_index)
    delta_x0 = max(float(np.std(ensemble[:, 0, alt_index])) * 0.15, 1.0)
    delta_max = max(float(np.percentile(ensemble[:, -1, alt_index], 90) - np.percentile(ensemble[:, -1, alt_index], 10)), delta_x0 * 8.0)
    try:
        t_star_s = predictability_horizon(max(lambda_hat, 1.0e-6), delta_max=delta_max, delta_x0=delta_x0)
    except ValueError:
        t_star_s = float("nan")

    final = _safe_positive(ensemble[:, -1, :])
    mean_final = _safe_positive(final.mean(axis=0))
    lo = _safe_positive(np.percentile(final, 10, axis=0))
    hi = _safe_positive(np.percentile(final, 90, axis=0))
    times_hr = t_grid_s / 3600.0
    spread = _safe_positive(np.percentile(ensemble[:, :, alt_index], 90, axis=0) - np.percentile(ensemble[:, :, alt_index], 10, axis=0))
    spread_fit_mask = times_hr > 1.0
    if np.count_nonzero(spread_fit_mask) < 3:
        spread_fit_mask = times_hr >= times_hr[1]
    slope, intercept = np.polyfit(times_hr[spread_fit_mask], np.log10(spread[spread_fit_mask]), 1)
    spread_fit = 10 ** (intercept + slope * times_hr)

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(11.6, 4.2),
        gridspec_kw={"width_ratios": [1.15, 1.15, 1.0]},
        constrained_layout=True,
    )

    ax = axes[0]
    ax.fill_betweenx(h_km, lo, hi, color="#2c7fb8", alpha=0.24, label="10-90% ensemble")
    ax.plot(mean_final, h_km, color="#145a86", linewidth=2.4, label="ensemble mean")
    ax.plot(deterministic[-1], h_km, color="#9c2f2f", linewidth=2.0, linestyle="--", label="deterministic")
    ax.plot(n0, h_km, color="0.25", linewidth=1.6, linestyle=":", label="initial profile")
    ax.set_xscale("log")
    ax.set_xlabel(r"Electron density $n$ [cm$^{-3}$]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Long-window profile")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    format_axes(ax)

    ax = axes[1]
    ax.fill_between(times_hr, np.percentile(ensemble[:, :, alt_index], 10, axis=0), np.percentile(ensemble[:, :, alt_index], 90, axis=0), color="#2c7fb8", alpha=0.22, label="10-90% band")
    ax.plot(times_hr, _safe_positive(ensemble[:, :, alt_index].mean(axis=0)), color="#145a86", linewidth=2.2, label="ensemble mean")
    ax.plot(times_hr, _safe_positive(deterministic[:, alt_index]), color="#9c2f2f", linewidth=2.0, linestyle="--", label="deterministic")
    if np.isfinite(t_star_s):
        ax.axvline(t_star_s / 3600.0, color="0.2", linestyle=":", linewidth=1.4)
        ax.text(t_star_s / 3600.0, ax.get_ylim()[1], r"$t_\ast$", ha="left", va="top", fontsize=8)
    ax.set_xlabel("Forecast lead time [h]")
    ax.set_ylabel(r"$n$ at 90 km [cm$^{-3}$]")
    ax.set_title(r"90 km spread and $t_\ast$")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    format_axes(ax)

    ax = axes[2]
    ax.plot(times_hr, np.log10(spread), color="#145a86", linewidth=2.2, label="log spread")
    ax.plot(times_hr, np.log10(spread_fit), color="#9c2f2f", linestyle="--", linewidth=2.0, label="linear fit")
    if np.isfinite(t_star_s):
        ax.axvline(t_star_s / 3600.0, color="0.25", linestyle=":", linewidth=1.4, label=r"$t_\ast$")
    ax.set_xlabel("Forecast lead time [h]")
    ax.set_ylabel(r"$\log_{10}$ spread")
    ax.set_title(r"Growth rate $\lambda$")
    ax.legend(frameon=False, fontsize=7.0, loc="upper left")
    format_axes(ax)
    ax.text(
        0.04,
        0.05,
        rf"$\hat\lambda={lambda_hat:.3g}\,\mathrm{{s}}^{{-1}}$",
        transform=ax.transAxes,
        fontsize=9,
        bbox=dict(facecolor="white", edgecolor="0.8", boxstyle="round,pad=0.25"),
    )

    fig.suptitle("Claim figure 02: stronger spread and explicit predictability horizon", y=1.02)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path, ensemble, t_grid_s


def _fig3_claim(output_path: Path, params: dict, ensemble: np.ndarray, t_grid_s: np.ndarray) -> Path:
    logger.info("Creating claim transfer-operator figure at {}", output_path)
    set_publication_style("nature")
    h_km = np.linspace(params["h_km_min"], params["h_km_max"], int(params["h_km_points"]))
    mean_field = ensemble.mean(axis=0).T
    eigs, modes = dmd_transfer_operator(mean_field, r=params["claim_fig3_rank"])

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(11.6, 4.1),
        gridspec_kw={"width_ratios": [1.0, 1.0, 1.15]},
        constrained_layout=True,
    )

    ax = axes[0]
    unit_circle = plt.Circle((0.0, 0.0), 1.0, color="0.8", fill=False, linestyle="--")
    ax.add_patch(unit_circle)
    ax.scatter(eigs.real, eigs.imag, c=np.abs(eigs), cmap="viridis", s=60, edgecolor="black")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Real part")
    ax.set_ylabel("Imaginary part")
    ax.set_title("DMD spectrum")
    format_axes(ax)

    ax = axes[1]
    mode = np.real(modes[:, 0])
    ax.plot(mode, h_km, color="#7b3294", linewidth=2.2)
    ax.set_xlabel("Mode amplitude")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Leading mode")
    format_axes(ax)

    ax = axes[2]
    im = ax.imshow(
        _safe_positive(mean_field),
        aspect="auto",
        origin="lower",
        extent=[t_grid_s[0] / 3600.0, t_grid_s[-1] / 3600.0, h_km[0], h_km[-1]],
        cmap="magma",
    )
    ax.set_xlabel("Time [h]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Ensemble-mean evolution")
    format_axes(ax, grid=False)
    cbar = fig.colorbar(im, ax=ax, pad=0.02, fraction=0.046)
    cbar.set_label(r"$\bar n(h,t)$ [cm$^{-3}$]")
    fig.suptitle("Claim figure 03: DMD from the Figure 02 ensemble mean", y=1.02)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path


def _run_gaussian_uq_ensemble(
    n0: np.ndarray,
    t_grid_s: np.ndarray,
    h_km: np.ndarray,
    P0_t,
    Q0_t,
    precip_model,
    params: dict,
    n_members: int,
    seed: int,
    ic_sigma: float,
    param_sigma: float,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    ensemble = np.empty((n_members, t_grid_s.size, h_km.size), dtype=float)
    alpha = float(params["fig4_alpha_cm3s"])
    beta = float(params["fig4_beta_s"])
    for member in range(n_members):
        n0_member = _safe_positive(n0 + rng.normal(0.0, ic_sigma, size=n0.shape))
        alpha_member = max(alpha * (1.0 + rng.normal(0.0, param_sigma)), 1.0e-12)
        beta_member = max(beta * (1.0 + rng.normal(0.0, param_sigma)), 1.0e-12)
        ensemble[member] = run_deterministic(
            n0=n0_member,
            t_grid_s=t_grid_s,
            h_km=h_km,
            P0_t=P0_t,
            Q0_t=Q0_t,
            precip_model=precip_model,
            h_m_km=params["h_m_km"],
            H_km=params["H_km"],
            chi_rad=0.0,
            alpha_cm3s=alpha_member,
            beta_s=beta_member,
        )
    return ensemble


def _fig4_claim(output_path: Path, params: dict) -> Path:
    logger.info("Creating claim exceedance figure at {}", output_path)
    set_publication_style("nature")
    h_km = np.linspace(params["fig4_h_km_min"], params["fig4_h_km_max"], int(params["fig4_h_km_points"]))
    t_grid_s = np.arange(0.0, params["fig4_t_end_s"] + params["fig4_t_step_s"], params["fig4_t_step_s"])
    n0 = np.full_like(h_km, params["fig4_n0_cm3"], dtype=float)
    P0_t = lambda t: params["fig4_P0_amp"]
    Q0_t = lambda t: params["fig4_Q0_amp"]
    precip_model = lambda h, t: gaussian_precipitation(
        h,
        t,
        Q0_t=Q0_t,
        h_p_km=params["fig4_precip_h_p_km"],
        H_p_km=params["fig4_precip_H_p_km"],
    )

    sde_ensemble = run_ensemble(
        n0=n0,
        t_grid_s=t_grid_s,
        h_km=h_km,
        P0_t=P0_t,
        Q0_t=Q0_t,
        precip_model=precip_model,
        h_m_km=params["h_m_km"],
        H_km=params["H_km"],
        chi_rad=0.0,
        alpha_cm3s=params["fig4_alpha_cm3s"],
        beta_s=params["fig4_beta_s"],
        sigma0=params["claim_fig4_sigma0"],
        beta_g=params["claim_fig4_beta_g"],
        P_max=params["claim_fig4_P_max"],
        n_members=params["claim_fig4_n_members"],
        seed=params["claim_fig4_seed"],
    )
    sde_ensemble = _safe_positive(np.nan_to_num(sde_ensemble, nan=np.nanmedian(n0), posinf=np.nanmax(n0) * 20.0, neginf=1.0))
    gaussian_ensemble = _run_gaussian_uq_ensemble(
        n0=n0,
        t_grid_s=t_grid_s,
        h_km=h_km,
        P0_t=P0_t,
        Q0_t=Q0_t,
        precip_model=precip_model,
        params=params,
        n_members=params["claim_fig4_n_members"],
        seed=params["claim_fig4_seed"] + 91,
        ic_sigma=params["claim_gauss_ic_sigma"],
        param_sigma=params["claim_gauss_param_sigma"],
    )
    gaussian_ensemble = _safe_positive(np.nan_to_num(gaussian_ensemble, nan=np.nanmedian(n0), posinf=np.nanmax(n0) * 20.0, neginf=1.0))

    sde_final = _safe_positive(sde_ensemble[:, -1, :])
    gauss_final = _safe_positive(gaussian_ensemble[:, -1, :])
    threshold_grid = np.linspace(
        min(np.percentile(sde_final, 30), np.percentile(gauss_final, 30)),
        max(np.percentile(sde_final, 97), np.percentile(gauss_final, 97)),
        80,
    )
    alt_index = int(np.argmin(np.abs(h_km - params["forecast_altitude_km"])))
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 7.4), constrained_layout=True)

    def _exceedance_map(ax, final, cmap, title):
        exceedance = np.array([(final > thr).mean(axis=0) for thr in threshold_grid])
        mesh = ax.contourf(
            threshold_grid,
            h_km,
            exceedance.T,
            levels=np.linspace(0.0, 1.0, 11),
            cmap=cmap,
            extend="neither",
        )
        ax.contour(
            threshold_grid,
            h_km,
            exceedance.T,
            levels=[0.25, 0.5, 0.75],
            colors=["#8c6d31", "#4d4d4d", "#08306b"],
            linewidths=[1.0, 1.2, 1.0],
        )
        ax.plot(np.median(final, axis=0), h_km, color="black", linewidth=1.6)
        ax.set_xlabel(r"Threshold $n_\ast$ [cm$^{-3}$]")
        ax.set_ylabel(r"Altitude [km]")
        ax.set_title(title)
        format_axes(ax, grid=False)
        return mesh

    mesh_sde = _exceedance_map(axes[0, 0], sde_final, "Blues", "SDE exceedance map")
    mesh_gauss = _exceedance_map(axes[0, 1], gauss_final, "Oranges", "Gaussian-UQ exceedance map")
    fig.colorbar(mesh_sde, ax=axes[0, 0], pad=0.02, fraction=0.046).set_label("Exceedance probability")
    fig.colorbar(mesh_gauss, ax=axes[0, 1], pad=0.02, fraction=0.046).set_label("Exceedance probability")

    def _tail_panel(ax, final, color, title):
        sorted_final = np.unique(np.sort(final[:, alt_index]))
        cdf = np.arange(1, sorted_final.size + 1) / sorted_final.size
        exceed = 1.0 - cdf
        if sorted_final.size >= 2:
            interp = PchipInterpolator(sorted_final, exceed, extrapolate=False)
            dense_x = np.linspace(sorted_final.min(), sorted_final.max(), 300)
            dense_y = np.clip(interp(dense_x), 0.0, 1.0)
        else:
            dense_x = sorted_final
            dense_y = exceed
        ax.plot(sorted_final, exceed, linestyle="none", marker="o", markersize=2.6, color=color, alpha=0.45)
        ax.plot(dense_x, dense_y, color=color, linewidth=2.1)
        ax.set_xscale("log")
        ax.set_xlabel(r"$n$ at 90 km [cm$^{-3}$]")
        ax.set_ylabel("Exceedance probability")
        ax.set_title(title)
        format_axes(ax)

    _tail_panel(axes[1, 0], sde_final, "#1f77b4", "SDE tail at 90 km")
    _tail_panel(axes[1, 1], gauss_final, "#d95f02", "Gaussian-UQ tail at 90 km")
    fig.suptitle("Claim figure 04: SDE versus Gaussian uncertainty", y=1.02)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path


def make_claim_figures(output_dir: Path, params: dict | None = None) -> list[Path]:
    """Generate the alternate numbered figure set and mirror it into docs."""

    logger.info("Generating claim figure set in {}", output_dir)
    if params is None:
        params = load_model_params()
    claim = _claim_params(params)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    fig1 = output_dir / "fig01_swmi_schematic.png"
    _fig1_claim(fig1, claim)
    mirror_figure_to_docs(fig1, docs_filename=fig1.name)
    written.append(fig1)

    fig2 = output_dir / "fig02_sde_ensemble.png"
    _, ensemble, t_grid_s = _fig2_claim(fig2, claim)
    mirror_figure_to_docs(fig2, docs_filename=fig2.name)
    written.append(fig2)

    fig3 = output_dir / "fig03_transfer_operator.png"
    _fig3_claim(fig3, claim, ensemble, t_grid_s)
    mirror_figure_to_docs(fig3, docs_filename=fig3.name)
    written.append(fig3)

    fig4 = output_dir / "fig04_exceedance.png"
    _fig4_claim(fig4, claim)
    mirror_figure_to_docs(fig4, docs_filename=fig4.name)
    written.append(fig4)

    logger.success("Wrote {} claim figures", len(written))
    return written


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "figures" / "output" / "claim",
        help="Directory where the claim-set PNGs will be written.",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    make_claim_figures(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
