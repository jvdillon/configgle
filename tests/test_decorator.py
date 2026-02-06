from __future__ import annotations

from configgle.decorator import autofig
from configgle.fig import Fig


def test_basic_decorator():
    @autofig
    class Foo:
        def __init__(self, x: int = 1, y: str = "default", z: float = 0.0):
            self.x = x
            self.y = y
            self.z = z

    assert Foo.Config.__bases__ == (Fig,)
    assert Foo.Config.parent_class == Foo

    config = Foo.Config(x=42, y="hello", z=3.14)
    assert config.x == 42
    assert config.y == "hello"
    assert config.z == 3.14

    foo = config.make()
    assert foo.x == 42
    assert foo.y == "hello"
    assert foo.z == 3.14


def test_config_update():
    @autofig
    class Foo:
        def __init__(self, x: int = 0, y: str = ""):
            self.x = x
            self.y = y

    config = Foo.Config(x=1, y="a")
    config.update(x=99)
    assert config.x == 99
    assert config.y == "a"


def test_with_defaults():
    @autofig
    class Bar:
        def __init__(
            self,
            items: list[int] | None = None,
            name: str = "",
            count: int = 5,
        ):
            self.items = items if items is not None else []
            self.name = name
            self.count = count

    assert Bar.Config.parent_class == Bar

    config = Bar.Config(items=[1, 2, 3], name="test")
    assert config.items == [1, 2, 3]
    assert config.name == "test"
    assert config.count == 5

    bar = config.make()
    assert bar.items == [1, 2, 3]
    assert bar.name == "test"
    assert bar.count == 5


def test_original_init_preserved():
    @autofig
    class Baz:
        def __init__(self, a: int = 0, b: str = ""):
            self.a = a
            self.b = b

    baz = Baz(a=10, b="direct")  # pyright: ignore[reportCallIssue]
    assert baz.a == 10  # pyright: ignore[reportAttributeAccessIssue]
    assert baz.b == "direct"  # pyright: ignore[reportAttributeAccessIssue]


def test_require_defaults():
    """Test that autofig with require_defaults=False allows parameters without defaults."""

    @autofig(require_defaults=False)
    class NoDefaults:
        def __init__(self, x: int):
            self.x = x

    # Should work - require_defaults=False allows parameters without defaults
    config = NoDefaults.Config(x=42)
    instance = config.make()
    assert instance.x == 42


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
