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
    def __get__(cls: type[_T], obj: object, owner: type[_ParentT]) -> type[_T]:
        return cls


class SetupableMeta2(type):
    def __get__(
        cls: type[_T], obj: object, owner: type[_ParentT]
    ) -> type[Setupable[_ParentT]]:
        return cls  # pyright: ignore[reportReturnType]


class SetupableMeta3(type):
    def __get__(
        cls: type[_T], obj: object, owner: type[_ParentT]
    ) -> type[_T | Setupable[_ParentT]]:
        return cls


class Fig1(Setupable[_ParentT], metaclass=SetupableMeta1):
    pass


class Fig2(Setupable[_ParentT], metaclass=SetupableMeta2):
    pass


class Fig3(Setupable[_ParentT], metaclass=SetupableMeta3):
    pass


class Foo1:
    class Config(Fig1):
        x: int = 0


reveal_type(Foo1.Config)
reveal_type(Foo1.Config().x)
reveal_type(Foo1.Config().setup())


class Foo2:
    class Config(Fig2):
        x: int = 0


reveal_type(Foo2.Config)
reveal_type(Foo2.Config().x)  # pyright: ignore[reportAttributeAccessIssue]
reveal_type(Foo2.Config().setup())


class Foo3:
    class Config(Fig3):
        x: int = 0


reveal_type(Foo3.Config)
reveal_type(Foo3.Config().x)  # pyright: ignore[reportAttributeAccessIssue]
reveal_type(Foo3.Config().setup())
