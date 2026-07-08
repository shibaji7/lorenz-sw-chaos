"""Synthetic forcing generators and optional loaders."""

from loguru import logger


logger.debug("Loaded forcing package")

from .lorenz_precip import lorenz63_precip_forcing
from .omni_loader import OmniUnavailableError, load_omni_index
from .soc_flare import soc_flare_forcing

__all__ = [
    "OmniUnavailableError",
    "lorenz63_precip_forcing",
    "load_omni_index",
    "soc_flare_forcing",
]
