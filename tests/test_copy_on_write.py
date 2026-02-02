"""Tests for configgle.copy_on_write."""

from __future__ import annotations

from typing import Self

import copy
import dataclasses

import pytest

from configgle.copy_on_write import CopyOnWrite


@dataclasses.dataclass
class SimpleConfig:
    """Simple config for testing."""

    value: int = 0
    name: str = "default"

    def finalize(self) -> Self:
        return copy.copy(self)


@dataclasses.dataclass
class NestedConfig:
    """Config with nested structure."""

    inner: SimpleConfig = dataclasses.field(default_factory=SimpleConfig)
    items: list[int] = dataclasses.field(default_factory=list)

    def finalize(self) -> Self:
        return copy.copy(self)


@dataclasses.dataclass
class DeeplyNestedConfig:
    """Config with deeply nested structure."""

    level1: NestedConfig = dataclasses.field(default_factory=NestedConfig)

    def finalize(self) -> Self:
        return copy.copy(self)


class TestCopyOnWriteBasic:
    """Test basic COW operations."""

    def test_read_without_copy(self):
        """Reading attributes should not trigger a copy."""
        original = SimpleConfig(value=42, name="test")
        with CopyOnWrite(original) as cow:
            _ = cow.value
            _ = cow.name
            assert cow._self_is_copy is False

        assert original.value == 42
        assert original.name == "test"

    def test_write_triggers_copy(self):
        """Writing an attribute should trigger a copy."""
        original = SimpleConfig(value=42, name="test")
        with CopyOnWrite(original) as cow:
            cow.value = 100
            assert cow._self_is_copy is True
            assert cow.unwrap.value == 100

        # Original unchanged
        assert original.value == 42

    def test_multiple_writes_single_copy(self):
        """Multiple writes should only copy once."""
        original = SimpleConfig(value=42, name="test")
        with CopyOnWrite(original) as cow:
            cow.value = 100
            cow.name = "modified"
            # Still the same copy
            assert cow._self_is_copy is True
            assert cow.unwrap.value == 100
            assert cow.unwrap.name == "modified"

        assert original.value == 42
        assert original.name == "test"


class TestCopyOnWriteNested:
    """Test COW with nested objects."""

    def test_nested_read_no_copy(self):
        """Reading nested attributes should not trigger copies."""
        original = NestedConfig(inner=SimpleConfig(value=42))
        with CopyOnWrite(original) as cow:
            _ = cow.inner.value
            assert cow._self_is_copy is False

    def test_nested_write_copies_chain(self):
        """Writing nested attribute should copy parent chain."""
        original = NestedConfig(inner=SimpleConfig(value=42))
        original_inner = original.inner

        with CopyOnWrite(original) as cow:
            cow.inner.value = 100

            # Both parent and child should be copied
            assert cow._self_is_copy is True
            inner_cow = cow._self_children.get("inner")
            assert inner_cow is not None
            assert inner_cow._self_is_copy is True

            # Values are updated
            assert cow.unwrap.inner.value == 100

        # Originals unchanged
        assert original.inner.value == 42
        assert original.inner is original_inner

    def test_deeply_nested_write(self):
        """Writing deeply nested attribute should copy entire chain."""
        original = DeeplyNestedConfig(level1=NestedConfig(inner=SimpleConfig(value=42)))

        with CopyOnWrite(original) as cow:
            cow.level1.inner.value = 100

            # Verify modification
            assert cow.unwrap.level1.inner.value == 100

        # Original unchanged
        assert original.level1.inner.value == 42


class TestCopyOnWriteSequences:
    """Test COW with sequences (lists, etc.)."""

    def test_list_read_no_copy(self):
        """Reading list items should not trigger copy."""
        original = NestedConfig(items=[1, 2, 3])
        with CopyOnWrite(original) as cow:
            _ = cow.items[0]
            assert cow._self_is_copy is False

    def test_list_setitem_triggers_copy(self):
        """Setting list item should trigger copy."""
        original = NestedConfig(items=[1, 2, 3])

        with CopyOnWrite(original) as cow:
            items_cow = cow.items
            items_cow[0] = 100

            assert items_cow._self_is_copy is True
            assert cow._self_is_copy is True
            assert cow.unwrap.items[0] == 100

        assert original.items[0] == 1

    def test_list_delitem_triggers_copy(self):
        """Deleting list item should trigger copy."""
        original = NestedConfig(items=[1, 2, 3])

        with CopyOnWrite(original) as cow:
            items_cow = cow.items
            del items_cow[0]

            assert items_cow._self_is_copy is True
            assert cow.unwrap.items == [2, 3]

        assert original.items == [1, 2, 3]


class TestCopyOnWriteMappings:
    """Test COW with mappings (dicts, etc.)."""

    def test_dict_read_no_copy(self):
        """Reading dict items should not trigger copy."""
        original = {"a": 1, "b": 2}
        with CopyOnWrite(original) as cow:
            _ = cow["a"]
            assert cow._self_is_copy is False

    def test_dict_setitem_triggers_copy(self):
        """Setting dict item should trigger copy."""
        original = {"a": 1, "b": 2}

        with CopyOnWrite(original) as cow:
            cow["a"] = 100
            assert cow._self_is_copy is True
            assert cow.unwrap["a"] == 100

        assert original["a"] == 1

    def test_dict_delitem_triggers_copy(self):
        """Deleting dict item should trigger copy."""
        original = {"a": 1, "b": 2}

        with CopyOnWrite(original) as cow:
            del cow["a"]
            assert cow._self_is_copy is True
            assert "a" not in cow.unwrap

        assert "a" in original


class TestCopyOnWriteDelattr:
    """Test COW with attribute deletion."""

    def test_delattr_triggers_copy(self):
        """Deleting an attribute should trigger copy."""

        class Deletable:
            def __init__(self):
                self.x = 1
                self.y = 2

        original = Deletable()

        with CopyOnWrite(original) as cow:
            del cow.x
            assert cow._self_is_copy is True
            assert not hasattr(cow.unwrap, "x")

        assert hasattr(original, "x")
        assert original.x == 1


class TestCopyOnWriteFinalize:
    """Test COW finalize integration."""

    def test_finalize_called_on_exit(self):
        """Finalize should be called on context exit if object has it."""
        finalize_called = []

        class FinalizeTracker:
            def __init__(self, value: int):
                self.value = value

            def finalize(self) -> Self:
                finalize_called.append(self.value)
                result = copy.copy(self)
                result.value *= 2
                return result

        original = FinalizeTracker(42)

        with CopyOnWrite(original):
            # No modification yet
            pass

        # Finalize should have been called
        assert 42 in finalize_called

    def test_finalize_not_called_twice(self):
        """Finalize should not be called if already finalized via method call."""
        finalize_count = [0]

        class FinalizeCounter:
            def __init__(self):
                self.value = 1

            def finalize(self) -> Self:
                finalize_count[0] += 1
                return copy.copy(self)

        original = FinalizeCounter()

        with CopyOnWrite(original) as cow:
            # Explicitly call finalize
            cow.finalize()

        # Should only be called once
        assert finalize_count[0] == 1


class TestCopyOnWriteMethodCalls:
    """Test COW with method calls."""

    def test_method_call_copies_first(self):
        """Method calls should copy before invoking."""

        class Counter:
            def __init__(self):
                self.count = 0

            def increment(self) -> int:
                self.count += 1
                return self.count

        original = Counter()

        with CopyOnWrite(original) as cow:
            result = cow.increment()
            assert result.unwrap == 1
            assert cow.unwrap.count == 1

        assert original.count == 0


class TestCopyOnWriteRepr:
    """Test COW representation."""

    def test_repr_delegates_to_wrapped(self):
        """Repr should delegate to wrapped object."""
        original = SimpleConfig(value=42)
        cow = CopyOnWrite(original)
        assert "SimpleConfig" in repr(cow)
        assert "42" in repr(cow)


class TestCopyOnWriteMultipleParents:
    """Test COW with objects having multiple parents."""

    def test_shared_child_multiple_parents(self):
        """A shared child should update all parent references on copy."""
        shared = SimpleConfig(value=42)

        @dataclasses.dataclass
        class Container:
            child: SimpleConfig = dataclasses.field(default_factory=SimpleConfig)

        container1 = Container(child=shared)
        container2 = Container(child=shared)

        # Create COW for both containers
        with CopyOnWrite(container1) as cow1, CopyOnWrite(container2) as cow2:
            # Get shared child through cow1
            child_cow = cow1.child

            # Register cow2 as another parent
            child_cow._self_parents.add((cow2, "child"))

            # Modify child
            child_cow.value = 100

            # Both parents should be copied
            assert cow1._self_is_copy is True
            assert cow2._self_is_copy is True

            # Both should point to the new child
            assert cow1.unwrap.child.value == 100
            assert cow2.unwrap.child.value == 100

        # Original shared child unchanged
        assert shared.value == 42


class TestCopyOnWriteDebugMode:
    """Test COW debug mode."""

    def test_debug_mode_prints(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Debug mode should print operations."""
        original = SimpleConfig(value=42)

        with CopyOnWrite(original, debug=True) as cow:
            _ = cow.value
            cow.value = 100

        captured = capsys.readouterr()
        assert "get" in captured.out.lower() or "value" in captured.out
        assert "set" in captured.out.lower() or "copy" in captured.out.lower()


class TestCopyOnWriteContextManager:
    """Test COW as context manager."""

    def test_returns_self_on_enter(self):
        """Context manager should return self on enter."""
        original = SimpleConfig()
        cow = CopyOnWrite(original)
        assert cow.__enter__() is cow

    def test_exits_children_first(self):
        """Children should be exited before parent."""
        exit_order = []

        class Trackable:
            def __init__(self, name: str):
                self.name = name
                self.child: Trackable | None = None

            def finalize(self) -> Self:
                exit_order.append(self.name)
                return copy.copy(self)

        parent = Trackable("parent")
        parent.child = Trackable("child")

        with CopyOnWrite(parent) as cow:
            # Access child to create wrapper
            _ = cow.child

        # Child should be finalized before parent
        assert exit_order.index("child") < exit_order.index("parent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
