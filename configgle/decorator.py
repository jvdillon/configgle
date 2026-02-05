"""Decorator to auto-generate a Config dataclass from __init__ parameters."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, get_type_hints, overload

import inspect

from configgle.custom_types import HasRelaxedConfig
from configgle.fig import Fig, FigMeta


if TYPE_CHECKING:
    from collections.abc import Callable


__all__ = ["autofig"]

_T = TypeVar("_T")


@overload
def autofig(
    cls: type[_T],
    /,
) -> type[HasRelaxedConfig[_T]]: ...


@overload
def autofig(
    cls: None = None,
    /,
    *,
    require_defaults: bool = True,
    kw_only: bool = True,
) -> Callable[[type[_T]], type[HasRelaxedConfig[_T]]]: ...


def autofig(
    cls: type[_T] | None = None,
    /,
    *,
    require_defaults: bool = True,
    kw_only: bool = True,
) -> type[HasRelaxedConfig[_T]] | Callable[[type[_T]], type[HasRelaxedConfig[_T]]]:
    """Decorator that inspects a class's __init__ method and creates a nested
    Config dataclass (subclassing Fig) with the same parameters.

    The Config class gets:
    - parent_class property (via SetupMeta)
    - setup() method to instantiate parent class via kwargs unpacking
    - finalize() for derived defaults
    - update() for config merging

    The original __init__ signature is preserved. Config.setup() unpacks
    the config fields as kwargs.

    Args:
        cls: The class to decorate (when used without arguments).
        require_defaults: If True, all Config fields must have defaults.
        kw_only: If True, all Config fields are keyword-only.

    Example:
        @autofig
        class Foo:
            def __init__(self, x: int, y: str = "default"):
                self.x = x
                self.y = y

        # Now you can use:
        config = Foo.Config(x=10, y="hello")
        foo = config.setup()  # Creates Foo(x=10, y="hello")

        # Or with arguments:
        @autofig(require_defaults=True, kw_only=True)
        class Bar:
            def __init__(self, x: int = 0):
                self.x = x

    """

    def decorator(cls_: type[_T]) -> type[HasRelaxedConfig[_T]]:
        sig = inspect.signature(cls_.__init__)
        try:
            type_hints = get_type_hints(cls_.__init__)
        except Exception:  # noqa: BLE001
            # get_type_hints can fail for various reasons (e.g., forward refs, missing imports)
            type_hints = {}

        annotations: dict[str, type] = {}
        defaults_: dict[str, object] = {}

        for i, (param_name, param) in enumerate(sig.parameters.items()):
            if i == 0:
                continue
            param_type = type_hints.get(param_name, object)
            annotations[param_name] = param_type
            if param.default is not inspect.Parameter.empty:
                defaults_[param_name] = param.default

        Config = FigMeta(
            "Config",
            (Fig,),
            {
                "__annotations__": annotations,
                "setup_with_kwargs": True,
                **defaults_,
            },
            require_defaults=require_defaults,
            kw_only=kw_only,
        )

        Config.__set_name__(cls_, "Config")
        cls_.Config = Config  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[unresolved-attribute]

        return cls_  # pyright: ignore[reportReturnType]

    if cls is None:
        # Called with arguments: @autofig(require_defaults=True)
        return decorator
    # Called without arguments: @autofig
    return decorator(cls)
