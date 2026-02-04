# uv run basedpyright demo.py
from __future__ import annotations

from typing import Any, Generic, reveal_type

from typing_extensions import TypeVar


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
