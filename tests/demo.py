"""Demo to show things we tried to preserve types.

To run:
  uv run basedpyright demo.py

tl;dr: Unless python has an intersection type you have to choose between:
    1. Status quo:
       - User specifically states the parent class type (current configgle).
       - Failing this, setup returns Any (again, current configgle).
    2. Fantasy land:
       - Python supports an intersection operator.
"""

from __future__ import annotations

from typing import (
    Annotated,
    Any,
    Generic,
    Protocol,
    overload,
    reveal_type,
)

from typing_extensions import TypeIs, TypeVar, override


_T = TypeVar("_T")
_ParentT = TypeVar("_ParentT", default=Any)


class Setupable(Generic[_ParentT]):
    def setup(self) -> _ParentT:
        raise NotImplementedError


class SetupableMeta1(type):
    # The following is the same as not having it at all but is here so you can
    # see the symmetry with other approaches.
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> type[_T]:
        return cls


class SetupableMeta2(type):
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> type[Setupable[_ParentT]]:
        return cls  # pyright: ignore[reportReturnType]


class SetupableMeta3(type):
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> type[_T | Setupable[_ParentT]]:
        return cls


# Symmetrically speaking the only one missing is
# `type[_T & Setupable[_ParentT]]` where `&` is an intersection (merge)
# operator and in fact that is exactly what we need.
# ...Too bad it doesn't exist.

# Note: Fig1 is the current choice of configgle.


class Fig1(Setupable[_ParentT], metaclass=SetupableMeta1):
    pass


class Fig2(Setupable[_ParentT], metaclass=SetupableMeta2):
    pass


class Fig3(Setupable[_ParentT], metaclass=SetupableMeta3):
    pass


# -------------------------------------------------------------------------------
# Fully works! ...But requires effort from user.
#
# Type of "Foo.Config" is "type[Config]"
# Type of "Foo.Config().x" is "int"
# Type of "Foo.Config().setup()" is "Foo"


class Foo:
    class Config(Fig1["Foo"]):
        x: int = 0


reveal_type(Foo.Config)
reveal_type(Foo.Config().x)
reveal_type(Foo.Config().setup())


# -------------------------------------------------------------------------------
# No errors or warnings! ...But loses type from setup.
#
# Type of "Foo1.Config" is "type[Config]"
# Type of "Foo1.Config().x" is "int"
# Type of "Foo1.Config().setup()" is "Any"


class Foo1:
    class Config(Fig1):
        x: int = 0


reveal_type(Foo1.Config)
reveal_type(Foo1.Config().x)
reveal_type(Foo1.Config().setup())


# -------------------------------------------------------------------------------
# Loses Config type.
#
# Type of "Foo2.Config" is "type[Setupable[Foo2]]"
# Type of "Foo2.Config().x" is "Unknown"
# Type of "Foo2.Config().setup()" is "Foo2"


class Foo2:
    class Config(Fig2):
        x: int = 0


reveal_type(Foo2.Config)
reveal_type(Foo2.Config().x)  # pyright: ignore[reportAttributeAccessIssue]
reveal_type(Foo2.Config().setup())


# -------------------------------------------------------------------------------
# Loses Config type and setup type.
#
# Type of "Foo3.Config" is "type[Config] | type[Setupable[Foo3]]"
# Type of "Foo3.Config().x" is "int | Unknown"
# Type of "Foo3.Config().setup()" is "Foo3 | Any"


class Foo3:
    class Config(Fig3):
        x: int = 0


reveal_type(Foo3.Config)
reveal_type(Foo3.Config().x)  # pyright: ignore[reportAttributeAccessIssue]
reveal_type(Foo3.Config().setup())


# -------------------------------------------------------------------------------
# IDEA 4: Protocol with __getattr__ to fake merge
#
# Result: setup() works, but x becomes Any via __getattr__
#
# (This is basically the RelaxedConfig idea.)
#
# Type of "Foo4.Config" is "type[ConfigProtocol4[Config, Foo4]]"
# Type of "Foo4.Config().x" is "Any"
# Type of "Foo4.Config().setup()" is "Foo4"


class ConfigProtocol4(  # pyright: ignore[reportInvalidTypeVarUse]
    Protocol[_T, _ParentT],
):
    """Protocol that has both Config fields (via __getattr__) and setup()."""

    def setup(self) -> _ParentT: ...
    def __getattr__(self, name: str) -> Any: ...


class SetupableMeta4(type):
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> type[ConfigProtocol4[_T, _ParentT]]:
        return cls  # pyright: ignore[reportReturnType]


class Fig4(Setupable[_ParentT], metaclass=SetupableMeta4):
    pass


class Foo4:
    class Config(Fig4):
        x: int = 0


reveal_type(Foo4.Config)
reveal_type(Foo4.Config().x)
reveal_type(Foo4.Config().setup())


# -------------------------------------------------------------------------------
# IDEA 5: @overload on __get__
#
# Result: Same as Idea 1 - overload doesn't help
#
# Type of "Foo5.Config" is "type[Config]"
# Type of "Foo5.Config().x" is "int"
# Type of "Foo5.Config().setup()" is "Any"


class SetupableMeta5(type):
    @overload
    def __get__(
        cls: type[_T],
        obj: None,
        owner: type[_ParentT],
    ) -> type[_T]: ...
    @overload
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> type[Setupable[_ParentT]]: ...
    def __get__(
        cls: type[_T],
        obj: object | None,
        owner: type[_ParentT],
    ) -> type[_T | Setupable[_ParentT]]:
        return cls


class Fig5(Setupable[_ParentT], metaclass=SetupableMeta5):
    pass


class Foo5:
    class Config(Fig5):
        x: int = 0


reveal_type(Foo5.Config)
reveal_type(Foo5.Config().x)
reveal_type(Foo5.Config().setup())


# -------------------------------------------------------------------------------
# IDEA 6: Annotated to carry extra type info
#
# Result: Annotated is ignored for type inference - same as Idea 1
#
# Type of "Foo6.Config" is "type[Config]"
# Type of "Foo6.Config().x" is "int"
# Type of "Foo6.Config().setup()" is "Any"


class ParentTypeMarker(Generic[_ParentT]):
    """Marker to carry parent type info in Annotated."""


class SetupableMeta6(type):
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> Annotated[type[_T], ParentTypeMarker[_ParentT]]:
        return cls


class Fig6(Setupable[_ParentT], metaclass=SetupableMeta6):
    pass


class Foo6:
    class Config(Fig6):
        x: int = 0


reveal_type(Foo6.Config)
reveal_type(Foo6.Config().x)
reveal_type(Foo6.Config().setup())


# -------------------------------------------------------------------------------
# IDEA 7: Manual override of setup() in each Config
#
# Result: WORKS! But requires even _more_ manual effort from user than option 1.
#
# Type of "Foo7.Config" is "type[Config]"
# Type of "Foo7.Config().x" is "int"
# Type of "Foo7.Config().setup()" is "Foo7"


class SetupableProtocol(Protocol[_ParentT]):  # pyright: ignore[reportInvalidTypeVarUse]
    def setup(self) -> _ParentT: ...


class SetupableMeta7(type):
    def __get__(
        cls: type[_T],
        obj: object,
        owner: type[_ParentT],
    ) -> type[_T]:
        return cls


class Fig7Base:
    def setup(self) -> Any:
        raise NotImplementedError


class Fig7(Fig7Base, metaclass=SetupableMeta7):
    pass


class Foo7:
    class Config(Fig7):
        x: int = 0

        @override
        def setup(self) -> Foo7:  # Manual override
            raise NotImplementedError


reveal_type(Foo7.Config)
reveal_type(Foo7.Config().x)
reveal_type(Foo7.Config().setup())


# -------------------------------------------------------------------------------
# IDEA 8: TypeIs for narrowing
#
# Result: TypeIs doesn't help - can't narrow class types this way
#
# Type of "Foo8.Config" is "type[Config]"
# Type of "Foo8.Config().x" is "int"
# Type of "Foo8.Config().setup()" is "Any"


def is_setupable(
    cls: type[_T],
    parent: type[_ParentT],
) -> TypeIs[type[Setupable[_ParentT]]]:  # pyright: ignore[reportGeneralTypeIssues]
    del cls, parent
    return True


class Foo8:
    class Config(Fig1):
        x: int = 0


reveal_type(Foo8.Config)
reveal_type(Foo8.Config().x)
reveal_type(Foo8.Config().setup())

# With TypeIs narrowing:
if is_setupable(Foo8.Config, Foo8):
    reveal_type(Foo8.Config)
    reveal_type(Foo8.Config().setup())


# -------------------------------------------------------------------------------
# IDEA 9: Decorator on parent class
#
# Result: setup() works! But x becomes Any (same as Idea 4)
#
# Type of "Foo9" is "type[Configurable9[Foo9]]"
# Type of "Foo9.Config" is "type[ConfigFor9[Foo9]]"
# Type of "Foo9.Config().x" is "Any"
# Type of "Foo9.Config().setup()" is "Foo9"


class ConfigFor9(Generic[_T]):
    """Tells type checker setup() returns _T."""

    def setup(self) -> _T: ...
    def __getattr__(self, name: str) -> Any: ...


class Configurable9(Generic[_T]):
    """Base class with typed Config."""

    Config: type[ConfigFor9[_T]]  # pyright: ignore[reportUninitializedInstanceVariable]


def has_config(cls: type[_T]) -> type[Configurable9[_T]]:
    return cls  # pyright: ignore[reportReturnType]


@has_config
class Foo9:
    class Config(Fig1):
        x: int = 0


reveal_type(Foo9)
reveal_type(Foo9.Config)  # pyright: ignore[reportGeneralTypeIssues]
reveal_type(Foo9.Config().x)  # pyright: ignore[reportGeneralTypeIssues]
reveal_type(Foo9.Config().setup())  # pyright: ignore[reportGeneralTypeIssues]
