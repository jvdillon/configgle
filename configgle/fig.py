from __future__ import annotations

from collections.abc import (
    Iterator,
    Mapping,
    Sequence,
    Set as AbstractSet,
)
from types import CellType, MethodType
from typing import (
    ClassVar,
    Self,
    TypeVar,
    cast,
    dataclass_transform,
)

import copy
import dataclasses

from typing_extensions import override

from configgle.custom_types import Configurable, DataclassLike
from configgle.inline import InlineConfig, PartialConfig
from configgle.pprinting import pformat
from configgle.traverse import recursively_iterate_over_object_descendants


__all__ = [
    "Dataclass",
    "Fig",
    "InlineConfig",
    "PartialConfig",
    "Setupable",
]


class SetupableMeta(type):
    """Metaclass that tracks the nested parent class for the Config pattern.

    Uses MethodType to bind the parent class reference, making parent_class
    immutable while remaining compatible with cloudpickle. This is a standard
    Python pattern for creating bound methods dynamically.

    See: https://docs.python.org/3/library/types.html#types.MethodType

    """

    @property
    def parent_class(cls) -> type | None:
        return cls._parent_class()

    def _parent_class(cls) -> type | None: ...

    def __set_name__(cls, owner: type, name: str) -> None:
        def _parent_class(cls: SetupableMeta) -> type:
            del cls
            return owner

        cls._parent_class = MethodType(_parent_class, cls)
        if owner_name := getattr(owner, "__name__", ""):
            cls.__name__ = f"{owner_name}.{name}"


class Setupable(metaclass=SetupableMeta):
    """Base class providing setup/finalize/update capabilities for configs.

    When nested inside a parent class, enables the pattern:
        instance = ParentClass.Config(...).setup()

    """

    __slots__: ClassVar[tuple[str, ...]] = ("_finalized",)
    setup_with_kwargs: ClassVar[bool] = False
    parent_class: ClassVar[type | None]

    def __init__(self):
        self._finalized = False

    def setup(self) -> object:
        """Finalize config and instantiate the parent class.

        Returns:
          instance: Instance of the parent class.

        Raises:
          ValueError: If not nested in a parent class.

        """
        config = self.finalize()
        cls = type(config).parent_class
        if cls is None:
            raise ValueError("Setupable class must be nested in a parent class")
        if getattr(type(config), "setup_with_kwargs", False):
            kwargs = {
                f.name: getattr(config, f.name)
                for f in dataclasses.fields(
                    cast("DataclassLike", cast("object", config)),
                )
            }
            return cls(**kwargs)
        return cls(config)

    def finalize(self) -> Self:
        """Create a finalized copy with derived defaults applied.

        Override this method to compute derived field values before instantiation.

        Returns:
          finalized: A shallow copy with _finalized=True.

        """
        r = copy.copy(self)

        for name in _get_object_attribute_names(r):
            try:
                value = getattr(r, name)
            except AttributeError:
                continue
            finalized_value = _finalize_value(value)
            if finalized_value is not value:
                # Use object.__setattr__ to bypass frozen dataclass restrictions
                object.__setattr__(r, name, finalized_value)

        # Use object.__setattr__ to bypass frozen dataclass restrictions
        object.__setattr__(r, "_finalized", True)
        return r

    def update(
        self,
        source: DataclassLike | Configurable[object] | None = None,
        *,
        skip_missing: bool = False,
        **kwargs: object,
    ) -> Self:
        """Update config attributes from source and/or kwargs.

        Args:
          source: Optional source object to copy attributes from.
          skip_missing: If True, skip kwargs keys that don't exist as attributes.
          **kwargs: Additional attribute overrides (use **mapping to pass a dict).

        Returns:
          self: Updated instance for method chaining.

        """
        # Build valid_keys set if needed for skip_missing
        valid_keys: set[str] | None = None
        if skip_missing:
            valid_keys = set(_get_object_attribute_names(self))

        # Apply source attributes (kwargs take precedence)
        if source is not None:
            for name in _get_object_attribute_names(source):
                # Skip if already in kwargs (kwargs override source)
                if name in kwargs:
                    continue
                # Skip if not a valid key
                if valid_keys is not None and name not in valid_keys:
                    continue
                try:
                    setattr(self, name, getattr(source, name))
                except AttributeError:
                    continue

        # Apply kwargs
        for k, v in kwargs.items():
            if valid_keys is not None and k not in valid_keys:
                continue
            setattr(self, k, v)

        return self

    def _repr_pretty_(self, p: object, cycle: bool) -> None:
        """IPython pretty printer hook for rich display in notebooks.

        Args:
          p: IPython RepresentationPrinter instance.
          cycle: True if a reference cycle is detected.

        """
        if cycle:
            # p is IPython's RepresentationPrinter, typed as object for optional dep
            p.text(  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
                f"{type(self).__name__}(...)",
            )
            return

        p.text(  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
            pformat(self),
        )


class _Default:
    __slots__: ClassVar[tuple[str, ...]] = ("value",)

    def __init__(self, value: object):
        self.value = value

    def __bool__(self) -> bool:
        return bool(self.value)

    @override
    def __repr__(self) -> str:
        return f"{self.value!r}"


class _DataclassParams:
    __mro__: ClassVar[list[type]]
    __name__: ClassVar[str]
    __slots__: ClassVar[tuple[str, ...]] = (
        "eq",
        "frozen",
        "init",
        "kw_only",
        "match_args",
        "order",
        "repr",
        "slots",
        "unsafe_hash",
        "weakref_slot",
    )

    def __init__(
        self,
        init: bool = True,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        match_args: bool = True,
        # The following differs from dataclasses.dataclass.
        kw_only: bool = True,
        slots: bool = True,
        weakref_slot: bool = True,
    ):
        self.init = init
        self.repr = repr
        self.eq = eq
        self.order = order
        self.unsafe_hash = unsafe_hash
        self.frozen = frozen
        self.match_args = match_args
        self.kw_only = kw_only
        self.slots = slots
        self.weakref_slot = weakref_slot

    @override
    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            + ", ".join(f"{k}={self[k]!r}" for k in self.keys())
            + ")"
        )

    def __getitem__(self, key: str) -> bool:
        return getattr(self, key)

    def __iter__(self) -> Iterator[str]:
        seen = set[str]()
        for c in type(self).__mro__:
            slots = getattr(c, "__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)
            for s in slots:
                if s in seen:
                    continue
                seen.update(s)
                yield s

    keys = __iter__

    @classmethod
    def create(
        cls,
        existing: _DataclassParams,
        **kwargs: bool | _Default,
    ) -> _DataclassParams:
        new = _DataclassParams()
        missing = object()
        for k in new:
            # Check kwargs first
            v = kwargs.get(k, missing)
            if v is missing or isinstance(v, _Default):
                # Fall back to existing
                v = getattr(existing, k, missing)
            if v is missing:
                continue
            setattr(new, k, bool(v))
        return new


_True = _Default(True)
_False = _Default(False)


class _DataclassMeta(type):
    __classcell__: CellType | None = None
    __dataclass_params__: _DataclassParams = _DataclassParams()

    def __new__(
        mcls: type[_DataclassMeta],
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, object],
        *,
        init: bool | _Default = _True,
        repr: bool | _Default = _True,
        eq: bool | _Default = _True,
        order: bool | _Default = _False,
        unsafe_hash: bool | _Default = _False,
        frozen: bool | _Default = _False,
        match_args: bool | _Default = _True,
        # The following differs from dataclasses.dataclass.
        kw_only: bool | _Default = _True,
        slots: bool | _Default = _True,
        weakref_slot: bool | _Default | None = None,
        require_defaults: bool = True,
    ) -> _DataclassMeta:
        cls = super().__new__(mcls, name, bases, attrs)
        if classcell := attrs.get("__classcell__"):
            cls.__classcell__ = cast("CellType", classcell)
        if "__slots__" in cls.__dict__:
            return cls
        kwargs = _DataclassParams.create(
            cls.__dataclass_params__,
            init=init,
            repr=repr,
            eq=eq,
            order=order,
            unsafe_hash=unsafe_hash,
            frozen=frozen,
            match_args=match_args,
            kw_only=kw_only,
            slots=slots,
            weakref_slot=slots if weakref_slot is None else weakref_slot,
        )
        cls = dataclasses.dataclass(cls, **kwargs)

        if require_defaults:
            current_annotations = cast(
                "dict[str, object]",
                attrs.get("__annotations__", {}),
            )
            for field in dataclasses.fields(cls):  # pyright: ignore[reportArgumentType]
                if field.name not in current_annotations:
                    continue
                if (
                    field.default is dataclasses.MISSING
                    and field.default_factory is dataclasses.MISSING
                ):
                    raise TypeError(
                        f"{name}.{field.name} must have a default value. "
                        f"Use require_defaults=False to disable this check.",
                    )

        cls.__dataclass_params__ = kwargs
        cls = cast("_DataclassMeta", cls)
        return cls


@dataclass_transform(kw_only_default=True)
class DataclassMeta(_DataclassMeta):
    """Public metaclass for creating dataclass-based config classes.

    This metaclass automatically applies @dataclass decorator with sensible
    defaults (kw_only=True, slots=True, etc.) to any class using it.

    """


class Dataclass(metaclass=DataclassMeta):
    """Base class that auto-applies @dataclass with sensible defaults."""

    __slots__: ClassVar[tuple[str, ...]] = ()


@dataclass_transform(kw_only_default=True)
class FigMeta(_DataclassMeta, SetupableMeta):
    """Combined metaclass for Fig.

    This metaclass combines _DataclassMeta (automatic dataclass conversion) and
    SetupableMeta (parent class tracking) to enable the nested Config pattern where
    Config classes can call .setup() to instantiate their parent class.

    """


class Fig(Setupable, metaclass=FigMeta):
    """Dataclass with setup/finalize/update for the nested Config pattern."""

    __slots__: ClassVar[tuple[str, ...]] = ()


_ValueT = TypeVar("_ValueT")


def _get_object_attribute_names(obj: object) -> Iterator[str]:
    """Get attribute names from an object via __slots__ or __dict__.

    Yields:
      name: Attribute name (excluding special attributes like __weakref__,
        __dict__, and _finalized).

    """
    for path, _ in recursively_iterate_over_object_descendants(
        obj,
        recurse=lambda path, _: len(path) <= 1,
    ):
        # Filter to string attribute names only (not integer indices from sequences)
        # Skip the root (empty path)
        if (
            len(path) == 1
            and isinstance(path[0], str)
            and path[0] not in ("__weakref__", "__dict__", "_finalized")
        ):
            yield path[0]


def _needs_finalization(x: object) -> bool:
    """Check if value needs finalization.

    Returns:
      needs_finalization: True if x has a finalize() method and either has no
        _finalized attribute or has _finalized=False.

    """
    return hasattr(x, "finalize") and not getattr(x, "_finalized", False)


def _finalize_value(value: _ValueT) -> _ValueT:
    """Recursively finalize values containing Fig instances.

    Uses traversal to discover all Fig instances in nested structures
    (sequences, mappings, sets, objects with __slots__/__dict__) and finalizes them.
    Preserves original container types.

    Args:
      value: Value to finalize recursively.

    Returns:
      finalized_value: Finalized copy of the value with all nested configs finalized.

    """
    if _needs_finalization(value):
        # Dynamic dispatch to finalize() checked by _needs_finalization
        return value.finalize()  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType,reportUnknownVariableType]

    # Skip classes and types - they don't need finalization
    if isinstance(value, type):
        return value

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        finalized_items: list[object] = [_finalize_value(v) for v in value]
        if isinstance(value, tuple):
            if type(value) is tuple:
                return tuple(finalized_items)  # pyright: ignore[reportReturnType]
            # Namedtuple needs unpacking
            return type(value)(*finalized_items)  # pyright: ignore[reportArgumentType]
        finalized = finalized_items
    elif isinstance(value, Mapping):
        # Mapping key type is unknown at runtime
        finalized = {k: _finalize_value(v) for k, v in value.items()}  # pyright: ignore[reportUnknownVariableType]
    elif isinstance(value, AbstractSet):
        finalized = {_finalize_value(v) for v in value}
    else:
        r = copy.copy(value)

        for name in _get_object_attribute_names(r):
            try:
                attr_value = getattr(r, name)
            except AttributeError:
                continue
            finalized_attr_value = _finalize_value(attr_value)
            if finalized_attr_value is not attr_value:
                object.__setattr__(r, name, finalized_attr_value)

        return r

    # Reconstruct container with finalized items
    return type(value)(finalized)  # pyright: ignore[reportCallIssue,reportUnknownArgumentType,reportUnknownVariableType]
