"""Custom types for config module."""

from __future__ import annotations

from typing import (
    ClassVar,
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
    "HasFinalize",
    "HasRelaxedConfig",
    "HasSetup",
    "RelaxedConfigurable",
]

_T_co = TypeVar("_T_co", covariant=True)
_T = TypeVar("_T")


# class _DataclassParamsProtocol(Protocol):
#     """Protocol for dataclasses._DataclassParams (private, Python 3.10+)."""
#
#     init: bool
#     repr: bool
#     eq: bool
#     order: bool
#     unsafe_hash: bool
#     frozen: bool
#     match_args: bool  # Python 3.10+
#     kw_only: bool  # Python 3.10+
#     slots: bool  # Python 3.10+
#     weakref_slot: bool  # Python 3.11+


@runtime_checkable
class DataclassLike(Protocol):
    """Protocol for objects that behave like dataclasses."""

    __dataclass_fields__: ClassVar[dict[str, dataclasses.Field[object]]]
    # __dataclass_params__: ClassVar[_DataclassParamsProtocol]  # Python 3.10+
    # __match_args__: ClassVar[tuple[str, ...]]  # When match_args=True (default)


@runtime_checkable
class HasFinalize(Protocol):
    """Protocol for objects with a finalize() method."""

    def finalize(self) -> Self: ...


@runtime_checkable
class HasSetup(Protocol):
    """Protocol for objects with a setup() method."""

    def setup(self) -> object: ...


@runtime_checkable
class Configurable(Protocol[_T_co]):
    """Protocol for config objects with setup/finalize/update methods."""

    _finalized: bool

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
