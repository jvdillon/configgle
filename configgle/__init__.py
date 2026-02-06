"""Configgle: Tools for making configurable Python classes for A/B experiments."""

from __future__ import annotations

from configgle.copy_on_write import CopyOnWrite
from configgle.custom_types import (
    DataclassLike,
    HasConfig,
    HasRelaxedConfig,
    Makeable,
    RelaxedConfigurable,
)
from configgle.decorator import autofig
from configgle.fig import Dataclass, Fig, Maker
from configgle.inline import InlineConfig, PartialConfig
from configgle.pprinting import pformat, pprint


__all__ = [
    "CopyOnWrite",
    "Dataclass",
    "DataclassLike",
    "Fig",
    "HasConfig",
    "HasRelaxedConfig",
    "InlineConfig",
    "Makeable",
    "Maker",
    "PartialConfig",
    "RelaxedConfigurable",
    "autofig",
    "pformat",
    "pprint",
]
