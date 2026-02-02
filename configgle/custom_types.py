"""Custom types for config module."""

from __future__ import annotations

from typing import (
    ClassVar,
    Final,
    Protocol,
    Self,
    TypeVar,
    runtime_checkable,
)

import dataclasses


__all__ = [
    "Configurable",
    "DataclassLike",
    "HasConfig",
    "HasRelaxedConfig",
    "RelaxedConfigurable",
]

_T_co = TypeVar("_T_co", covariant=True)
_T = TypeVar("_T")


@runtime_checkable
@dataclasses.dataclass(init=False, repr=False, eq=False)
class DataclassLike(Protocol):
    """Protocol for objects that behave like dataclasses."""


@runtime_checkable
class Configurable(Protocol[_T_co]):
    """Protocol for config objects with setup/finalize/update methods."""

    _finalized: Final[bool]

    def setup(self) -> _T_co: ...
    def finalize(self) -> Self: ...
    def update(
        self,
        source: DataclassLike | Configurable[object] | None = None,
        *,
        skip_missing: bool = False,
        **kwargs: object,
    ) -> Self: ...


@runtime_checkable
class HasConfig(Protocol[_T]):
    """Protocol for classes with a typed Config nested class."""

    Config: ClassVar[type[Configurable[_T]]]  # pyright: ignore[reportGeneralTypeIssues]


@runtime_checkable
class RelaxedConfigurable(Configurable[_T], Protocol):
    """Protocol for auto-generated Config classes.

    Extends Configurable with __init__ and __getattr__ to support
    dynamic field access without requiring suppressions in user code.
    """

    parent_class: ClassVar[type[_T] | None]  # pyright: ignore[reportGeneralTypeIssues]

    def __init__(self, *args: object, **kwargs: object) -> None: ...
    def __getattr__(self, name: str) -> object: ...


@runtime_checkable
class HasRelaxedConfig(Protocol[_T]):
    """Protocol for classes decorated with @autofig."""

    Config: ClassVar[type[RelaxedConfigurable[_T]]]  # pyright: ignore[reportGeneralTypeIssues]
