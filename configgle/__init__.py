"""Configgle: Tools for making configurable Python classes for A/B experiments."""

from configgle.copy_on_write import CopyOnWrite
from configgle.custom_types import (
    Configurable,
    DataclassLike,
    HasConfig,
    HasRelaxedConfig,
    RelaxedConfigurable,
)
from configgle.decorator import autofig
from configgle.fig import (
    Fig,
    InlineConfig,
    PartialConfig,
    Setupable,
)
from configgle.pprinting import pformat, pprint


__all__ = [
    "Configurable",
    "CopyOnWrite",
    "DataclassLike",
    "Fig",
    "HasConfig",
    "HasRelaxedConfig",
    "InlineConfig",
    "PartialConfig",
    "RelaxedConfigurable",
    "Setupable",
    "autofig",
    "pformat",
    "pprint",
]
