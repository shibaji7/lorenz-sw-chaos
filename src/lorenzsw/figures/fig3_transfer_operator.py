"""Figure 3 transfer-operator entry point."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from loguru import logger

from .._logging import configure_logging
from ..model_params import load_model_params
from ..plotting import format_axes, set_publication_style
from ..scenarios import build_chaotic_scenario
from ..transfer_operator import dmd_transfer_operator


logger.debug("Loaded fig3 module")


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    logger.info("Creating transfer-operator figure at {}", output_path)
    set_publication_style("nature")
    if params is None:
        params = load_model_params()

    scenario = build_chaotic_scenario(params)
    h_km = scenario.h_km
    # DMD wants (n_features, n_time). Use the deterministic response to the SOC +
    # Lorenz-63 forcing so the spectrum reflects the same run shown in Fig. 2,
    # rather than an unrelated synthetic signal.
    snapshots = scenario.deterministic.T

    eigs, modes = dmd_transfer_operator(snapshots, r=int(params["fig3_dmd_rank"]))

    fig, axes = plt.subplots(1, 2, figsize=(params["fig3_figure_width_in"], params["fig3_figure_height_in"]))
    ax = axes[0]
    unit_circle = plt.Circle((0.0, 0.0), 1.0, color="0.8", fill=False, linestyle="--")
    ax.add_patch(unit_circle)
    ax.scatter(eigs.real, eigs.imag, c=np.abs(eigs), cmap="viridis", s=55, edgecolor="black")
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Real part")
    ax.set_ylabel("Imaginary part")
    ax.set_title("DMD spectrum")
    format_axes(ax)

    ax = axes[1]
    mode = np.real(modes[:, 0])
    ax.plot(mode, h_km, color="tab:purple", linewidth=2.2)
    ax.set_xlabel("Mode amplitude")
    ax.set_ylabel(r"Altitude [km]")
    ax.set_title("Leading DMD mode")
    format_axes(ax)

    fig.suptitle("Transfer-operator approximation via DMD (SOC + Lorenz-63 forced run)", y=1.03)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path
