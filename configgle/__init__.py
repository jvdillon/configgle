"""Configgle: Tools for making configurable Python classes for A/B experiments."""

from __future__ import annotations

from configgle.copy_on_write import CopyOnWrite
from configgle.custom_types import (
    Configurable,
    DataclassLike,
    HasConfig,
    HasFinalize,
    HasRelaxedConfig,
    HasSetup,
    RelaxedConfigurable,
)
from configgle.decorator import autofig
from configgle.fig import Dataclass, Fig, Setupable
from configgle.inline import InlineConfig, PartialConfig
from configgle.pprinting import pformat, pprint


__all__ = [
    "Configurable",
    "CopyOnWrite",
    "Dataclass",
    "DataclassLike",
    "Fig",
    "HasConfig",
    "HasFinalize",
    "HasRelaxedConfig",
    "HasSetup",
    "InlineConfig",
    "PartialConfig",
    "RelaxedConfigurable",
    "Setupable",
    "autofig",
    "pformat",
    "pprint",
]
