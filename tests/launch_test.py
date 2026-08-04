from __future__ import annotations

from dataclasses import field

import pytest

from configgle import Fig, Makeable
from configgle.launch import resolve_config


class Child:
    class Config(Fig["Child"]):
        lr: float = 1e-3

    def __init__(self, config: Config):
        self.lr = config.lr


class Trainer:
    class Config(Fig["Trainer"]):
        steps: int = 100
        child: Child.Config = field(default_factory=Child.Config)

    def __init__(self, config: Config):
        self.config = config


def baseline() -> Makeable[Trainer]:
    """Factory returning a fresh config, as the launcher expects."""
    return Trainer.Config()


not_a_callable = 42


def returns_non_config() -> int:
    return 42


def test_resolve_config_returns_the_factory_result() -> None:
    config = resolve_config(f"{__name__}.baseline")
    assert isinstance(config, Trainer.Config)
    assert config.steps == 100


def test_resolve_config_returns_a_fresh_config_each_call() -> None:
    """Two resolves must not share mutable state, or one run leaks into the next."""
    first = resolve_config(f"{__name__}.baseline")
    second = resolve_config(f"{__name__}.baseline")
    assert isinstance(first, Trainer.Config)
    assert isinstance(second, Trainer.Config)
    assert first is not second
    assert first.child is not second.child


def test_resolve_config_undotted_path_raises() -> None:
    with pytest.raises(ValueError, match="is not a dotted path"):
        resolve_config("baseline")


def test_resolve_config_missing_module_raises() -> None:
    with pytest.raises(ImportError, match="Cannot import module"):
        resolve_config("configgle_no_such_module.baseline")


def test_resolve_config_missing_attribute_raises() -> None:
    with pytest.raises(AttributeError, match="has no attribute"):
        resolve_config(f"{__name__}.no_such_function")


def test_resolve_config_non_callable_raises() -> None:
    with pytest.raises(TypeError, match="is not callable"):
        resolve_config(f"{__name__}.not_a_callable")


def test_resolve_config_non_config_return_raises() -> None:
    with pytest.raises(TypeError, match="not a config"):
        resolve_config(f"{__name__}.returns_non_config")


def test_resolve_config_composes_with_overrides_and_make() -> None:
    """The launcher's whole contract: resolve -> override -> make."""
    from configgle import apply_overrides  # noqa: PLC0415

    config = resolve_config(f"{__name__}.baseline")
    apply_overrides(config, ["steps=5", "child.lr=3e-4"])
    trainer = config.make()
    assert isinstance(trainer, Trainer)
    assert trainer.config.steps == 5
    assert trainer.config.child.lr == 3e-4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
