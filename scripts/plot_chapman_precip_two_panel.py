"""Generate a two-panel figure for Chapman and precipitation proxy profiles."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from loguru import logger

os.environ.setdefault("MPLCONFIGDIR", str(Path("/tmp") / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(Path("/tmp") / "xdg-cache"))

Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from lorenzsw._logging import configure_logging
from lorenzsw.chapman import chapman_production
from lorenzsw.model_params import load_model_params
from lorenzsw.precipitation import gaussian_precipitation
from lorenzsw.plotting import format_axes, set_publication_style
from _source_term_plot_utils import save_figure_pair

set_publication_style("nature")


def equilibrium_density(
    production: np.ndarray,
    alpha_cm3s: float,
    beta_s: float,
) -> np.ndarray:
    production = np.asarray(production, dtype=float)
    if alpha_cm3s < 0:
        raise ValueError("alpha_cm3s must be non-negative.")
    if beta_s < 0:
        raise ValueError("beta_s must be non-negative.")

    if alpha_cm3s == 0:
        if beta_s == 0:
            return np.zeros_like(production)
        return production / beta_s

    disc = beta_s**2 + 4.0 * alpha_cm3s * np.maximum(production, 0.0)
    return (-beta_s + np.sqrt(disc)) / (2.0 * alpha_cm3s)


def build_profiles(params: dict | None = None):
    if params is None:
        params = load_model_params()

    h_km = np.linspace(
        params["profile_h_km_min"],
        params["profile_h_km_max"],
        int(params["profile_h_km_points"]),
    )
    solar_peak = params["profile_solar_peak_amp"]
    precip_energy = params["profile_precip_amp"]

    logger.info("Building Chapman and precipitation profile data")
    P_solar = chapman_production(
        h_km,
        t_s=0.0,
        P0_t=lambda t: solar_peak,
        h_m_km=params["profile_chapman_h_m_km"],
        H_km=params["profile_chapman_H_km"],
        chi_rad=params["profile_chi_rad"],
    )
    P_precip = gaussian_precipitation(
        h_km,
        t_s=0.0,
        Q0_t=lambda t: precip_energy,
        h_p_km=params["profile_precip_h_p_km"],
        H_p_km=params["profile_precip_H_p_km"],
    )

    alpha_cm3s = params["profile_alpha_cm3s"]
    beta_s = params["profile_beta_s"]

    n_solar = equilibrium_density(P_solar, alpha_cm3s, beta_s)
    n_precip = equilibrium_density(P_precip, alpha_cm3s, beta_s)

    return h_km, n_solar, n_precip, P_precip


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating two-panel Chapman/precipitation figure at {}", output_path)
    if params is None:
        params = load_model_params()
    h_km, n_solar, n_precip, P_precip = build_profiles(params)

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(params["profile_two_panel_figure_width_in"], params["profile_two_panel_figure_height_in"]),
        sharey=True,
    )

    panels = [
        (axes[0], n_solar, "Chapman solar profile", "tab:blue"),
        (axes[1], n_precip, "Parameterized precipitation proxy", "tab:orange"),
    ]

    for idx, (ax, density, title, color) in enumerate(panels):
        ax.plot(density, h_km, linewidth=2.4, color=color)
        ax.set_xscale("log")
        ax.set_title(title)
        ax.set_xlabel(r"Electron density $n$ [cm$^{-3}$]")
        ax.set_xlim(left=max(density.min() * 0.8, 1e-4))
        ax.text(
            0.03,
            0.95,
            f"({chr(ord('a') + idx)})",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=11,
            fontweight="bold",
        )
        format_axes(ax)

    precip_axis = axes[1].twiny()
    precip_axis.plot(P_precip, h_km, linewidth=1.9, color="tab:red", linestyle="--")
    precip_axis.set_xscale("log")
    precip_axis.set_xlabel(r"Precipitation production $P_{\mathrm{precip}}$ [cm$^{-3}$ s$^{-1}$]")
    precip_axis.tick_params(axis="x", colors="tab:red")
    precip_axis.xaxis.label.set_color("tab:red")
    precip_axis.set_xlim(left=max(P_precip.min() * 0.8, 1e-8))
    precip_axis.set_ylim(h_km.min(), h_km.max())

    axes[0].set_ylabel(r"Altitude [km]")
    axes[0].set_ylim(h_km.min(), h_km.max())
    axes[1].tick_params(labelleft=False)

    fig.suptitle("Chapman and precipitation height profiles", y=1.02)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_figure_pair(fig, output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "figures" / "output",
        help="Directory where the PNG will be written.",
    )
    parser.add_argument(
        "--filename",
        type=str,
        default="chapman_precip_two_panel.png",
        help="Output PNG filename.",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    output_path = args.output_dir / args.filename
    make_figure(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
