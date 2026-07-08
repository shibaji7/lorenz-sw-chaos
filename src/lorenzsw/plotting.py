"""Shared plotting style helpers for publication figures."""

from __future__ import annotations

from typing import Literal

import matplotlib.pyplot as plt
from loguru import logger


PublicationStyle = Literal["nature", "agu", "paper"]


def set_publication_style(style: PublicationStyle = "nature") -> None:
    """Apply a clean publication-oriented Matplotlib style."""

    logger.debug("Applying publication style: {}", style)
    try:
        import scienceplots  # noqa: F401

        if style == "agu":
            plt.style.use(["science", "no-latex"])
        else:
            plt.style.use(["nature", "no-latex"])
    except Exception:
        plt.style.use("default")

    plt.rcParams.update(
        {
            "axes.grid": False,
            "axes.linewidth": 0.8,
            "axes.labelsize": 10,
            "axes.facecolor": "white",
            "axes.titlesize": 11,
            "figure.facecolor": "white",
            "figure.dpi": 200,
            "font.size": 9,
            "legend.frameon": False,
            "legend.handlelength": 2.0,
            "lines.linewidth": 1.8,
            "savefig.dpi": 300,
            "savefig.facecolor": "white",
            "savefig.edgecolor": "white",
            "xtick.direction": "in",
            "ytick.direction": "in",
            "xtick.major.size": 4,
            "ytick.major.size": 4,
            "xtick.minor.size": 2,
            "ytick.minor.size": 2,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "xtick.minor.width": 0.6,
            "ytick.minor.width": 0.6,
        }
    )


def format_axes(ax, *, grid: bool = False, grid_alpha: float = 0.12, grid_linewidth: float = 0.5) -> None:
    """Apply a clean journal-style axis treatment."""

    ax.minorticks_on()
    ax.tick_params(which="both", direction="in", top=True, right=True)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)
    ax.set_axisbelow(True)
    if grid:
        ax.grid(
            True,
            which="major",
            linestyle="-",
            linewidth=grid_linewidth,
            alpha=grid_alpha,
        )
    else:
        ax.grid(False)
    ax.set_facecolor("white")
