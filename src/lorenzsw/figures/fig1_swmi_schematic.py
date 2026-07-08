"""Figure 1 schematic entry point."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from loguru import logger


logger.debug("Loaded fig1 module")


def make_figure(output_path: Path, params: dict | None = None) -> Path:
    """Draw a simple SW-M-I schematic with labeled flow arrows."""

    logger.info("Creating SW-M-I schematic at {}", output_path)
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.set_axis_off()

    boxes = {
        "Sun / forcing": (0.08, 0.62, 0.18, 0.16, "#f4a261"),
        "Ionization": (0.34, 0.66, 0.18, 0.16, "#2a9d8f"),
        "Ionosphere\n$n(h,t)$": (0.58, 0.58, 0.20, 0.22, "#264653"),
        "Observables": (0.82, 0.64, 0.14, 0.14, "#e76f51"),
    }
    for label, (x, y, w, h, color) in boxes.items():
        rect = plt.Rectangle((x, y), w, h, facecolor=color, edgecolor="black", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", color="white", fontsize=11)

    arrows = [
        ((0.26, 0.70), (0.34, 0.74), "photoionization"),
        ((0.52, 0.72), (0.58, 0.69), "continuity / SDE"),
        ((0.78, 0.69), (0.82, 0.71), "data comparison"),
        ((0.68, 0.58), (0.68, 0.38), "recombination + loss"),
        ((0.40, 0.58), (0.40, 0.38), "precipitation forcing"),
    ]
    for start, end, text in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops=dict(arrowstyle="->", linewidth=1.8))
        ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.03, text, ha="center", fontsize=8)

    ax.text(
        0.5,
        0.15,
        "Conceptual pipeline: solar + precipitation forcing drive a stochastic continuity equation.",
        ha="center",
        fontsize=10,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    logger.success("Wrote {}", output_path)
    return output_path
