"""Generate a dedicated Chapman photoionization term figure."""

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
from lorenzsw.plotting import format_axes, set_publication_style
from _source_term_plot_utils import equilibrium_density, mirror_figure_to_docs, save_figure_pair


set_publication_style("nature")


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating Chapman photoionization term figure at {}", output_path)
    if params is None:
        params = load_model_params()

    h_km = np.linspace(
        params["profile_h_km_min"],
        params["profile_h_km_max"],
        int(params["profile_h_km_points"]),
    )

    P_solar = chapman_production(
        h_km,
        t_s=0.0,
        P0_t=lambda t: params["profile_solar_peak_amp"],
        h_m_km=params["profile_chapman_h_m_km"],
        H_km=params["profile_chapman_H_km"],
        chi_rad=params["profile_chi_rad"],
    )
    n_solar = equilibrium_density(P_solar, params["profile_alpha_cm3s"], params["profile_beta_s"])

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(params["profile_two_panel_figure_width_in"], params["profile_two_panel_figure_height_in"]),
        sharey=True,
    )

    ax = axes[0]
    ax.plot(P_solar, h_km, color="tab:blue", linewidth=2.4)
    ax.set_xscale("log")
    ax.set_xlabel(r"Photoionization production $P_{\mathrm{solar}}$ [cm$^{-3}$ s$^{-1}$]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Chapman photoionization term")
    ax.text(
        0.03,
        0.95,
        "(a)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlim(left=max(P_solar.min() * 0.8, 1e-8))
    format_axes(ax)

    ax = axes[1]
    ax.plot(n_solar, h_km, color="tab:green", linewidth=2.4)
    ax.set_xscale("log")
    ax.set_xlabel(r"Implied equilibrium density $n_\ast$ [cm$^{-3}$]")
    ax.set_title("Equilibrium response to photoionization")
    ax.text(
        0.03,
        0.95,
        "(b)",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=11,
        fontweight="bold",
    )
    ax.set_xlim(left=max(n_solar.min() * 0.8, 1e-4))
    ax.tick_params(labelleft=False)
    format_axes(ax)

    fig.suptitle("Chapman photoionization: source term and density response", y=1.02)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_figure_pair(fig, output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    mirror_figure_to_docs(output_path, "chapman_photoionization_term.png")
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
        default="chapman_photoionization_term.png",
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
