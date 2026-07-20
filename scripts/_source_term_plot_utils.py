"""Helpers for standalone source-term plotting scripts."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_FIGURES_DIR = REPO_ROOT / "docs" / "assets" / "figures"


def equilibrium_density(production: np.ndarray, alpha_cm3s: float, beta_s: float) -> np.ndarray:
    """Return the positive equilibrium density implied by a source term."""

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


def mirror_figure_to_docs(output_path: Path, docs_filename: str | None = None) -> Path:
    """Copy a figure into the docs asset tree for MkDocs rendering."""

    DOCS_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    docs_path = DOCS_FIGURES_DIR / (docs_filename or output_path.name)
    shutil.copy2(output_path, docs_path)
    return docs_path


def save_figure_pair(
    fig: plt.Figure,
    output_path: Path,
    *,
    dpi: int = 200,
    bbox_inches: str | None = "tight",
    tiff_dpi: int | None = None,
) -> tuple[Path, Path]:
    """Save a figure as both PNG and TIFF using the same basename."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = output_path.with_suffix(".png")
    tif_path = output_path.with_suffix(".tif")
    fig.savefig(png_path, dpi=dpi, bbox_inches=bbox_inches)
    fig.savefig(tif_path, dpi=tiff_dpi or dpi, bbox_inches=bbox_inches, format="tiff")
    return png_path, tif_path
