"""Generate a dedicated precipitation source-term figure."""

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
from lorenzsw.model_params import load_model_params
from lorenzsw.plotting import format_axes, set_publication_style
from lorenzsw.precipitation import gaussian_precipitation
from _source_term_plot_utils import equilibrium_density, mirror_figure_to_docs, save_figure_pair


set_publication_style("nature")


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating precipitation term figure at {}", output_path)
    if params is None:
        params = load_model_params()

    h_km = np.linspace(
        params["profile_h_km_min"],
        params["profile_h_km_max"],
        int(params["profile_h_km_points"]),
    )

    P_precip = gaussian_precipitation(
        h_km,
        t_s=0.0,
        Q0_t=lambda t: params["profile_precip_amp"],
        h_p_km=params["profile_precip_h_p_km"],
        H_p_km=params["profile_precip_H_p_km"],
    )
    n_precip = equilibrium_density(P_precip, params["profile_alpha_cm3s"], params["profile_beta_s"])

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(params["profile_two_panel_figure_width_in"], params["profile_two_panel_figure_height_in"]),
        sharey=True,
    )

    ax = axes[0]
    ax.plot(P_precip, h_km, color="tab:red", linewidth=2.4)
    ax.set_xscale("log")
    ax.set_xlabel(r"Precipitation production $P_{\mathrm{precip}}$ [cm$^{-3}$ s$^{-1}$]")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Gaussian precipitation proxy")
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
    ax.set_xlim(left=max(P_precip.min() * 0.8, 1e-8))
    format_axes(ax)

    ax = axes[1]
    ax.plot(n_precip, h_km, color="tab:orange", linewidth=2.4)
    ax.set_xscale("log")
    ax.set_xlabel(r"Implied equilibrium density $n_\ast$ [cm$^{-3}$]")
    ax.set_title("Equilibrium response to precipitation")
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
    ax.set_xlim(left=max(n_precip.min() * 0.8, 1e-4))
    ax.tick_params(labelleft=False)
    format_axes(ax)

    fig.suptitle("Precipitation source term and density response", y=1.02)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_figure_pair(fig, output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    mirror_figure_to_docs(output_path, "precipitation_term.png")
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
        default="precipitation_term.png",
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
