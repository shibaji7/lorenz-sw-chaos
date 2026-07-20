"""Generate electron density height profiles for Chapman and precipitation forcing."""

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

from lorenzsw.chapman import chapman_production
from lorenzsw._logging import configure_logging
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
    """Return the positive equilibrium density implied by the continuity drift."""

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
    n_combined = equilibrium_density(P_solar + P_precip, alpha_cm3s, beta_s)

    return h_km, n_solar, n_precip, n_combined


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating electron density profile figure at {}", output_path)
    if params is None:
        params = load_model_params()
    h_km, n_solar, n_precip, n_combined = build_profiles(params)

    fig, ax = plt.subplots(
        figsize=(params["profile_single_figure_width_in"], params["profile_single_figure_height_in"])
    )
    ax.plot(n_solar, h_km, label="Chapman solar", linewidth=2.2)
    ax.plot(n_precip, h_km, label="Precipitation", linewidth=2.2)
    ax.plot(n_combined, h_km, label="Combined", linewidth=2.4)

    ax.set_xscale("log")
    ax.set_xlabel(r"Electron density $n$ [cm$^{-3}$]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Electron density height profiles")
    ax.legend(frameon=False, loc="lower right")
    format_axes(ax)

    text = r"$P_{\mathrm{solar}}$ Chapman profile, $P_{\mathrm{precip}}$ Gaussian precipitation proxy"
    ax.text(
        0.02,
        0.02,
        text,
        transform=ax.transAxes,
        fontsize=9,
        ha="left",
        va="bottom",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8, edgecolor="0.8"),
    )

    ax.set_ylim(h_km.min(), h_km.max())
    ax.set_xlim(left=max(np.min([n_solar.min(), n_precip.min(), n_combined.min()]) * 0.8, 1e-4))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    save_figure_pair(fig, output_path, dpi=200)
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
        default="electron_density_profiles.png",
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
