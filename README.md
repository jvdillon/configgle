# configgle🤭

[![PyPI version](https://img.shields.io/pypi/v/configgle.svg)](https://pypi.org/project/configgle/)
[![CI](https://github.com/rekursiv-ai/configgle/actions/workflows/package-validation.yml/badge.svg?branch=main)](https://github.com/rekursiv-ai/configgle/actions/workflows/package-validation.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Discord](https://img.shields.io/discord/1530237005311639592?logo=discord&logoColor=white&label=Discord&color=5865F2)](https://discord.gg/2GZFPPvCqn)

Type-safe hierarchical experiment configuration using pure Python dataclass factories and dependency injection.

## Quick Start

```bash
# Mac:
#   # Required for quick install.
#   brew install uv

# Ubuntu/Debian:
#   # Required for quick install.
#   sudo apt-get install -y curl
#   curl -LsSf https://astral.sh/uv/install.sh | sh

uv add configgle

# Alternatively: python -m pip install configgle
```

Hierarchical experiment configuration using pure Python dataclasses with typed
factory methods, covariant protocols, inheritance support, and tooling for
pretty printing, autodecorating, updating, and semi-deep copying.

## Example

```python
from configgle import Fig


class Model:
    class Config(Fig):
        hidden_size: int = 256
        num_layers: int = 4

    def __init__(self, config: Config):
        self.config = config


# Create and modify config
cfg = Model.Config()
cfg.hidden_size = 512

# Instantiate the parent class
model = cfg.make()
print(model.config)
assert isinstance(model, Model)
```

Configs are plain mutable dataclasses, so experiments are just functions that
tweak a baseline:

```python
def exp000() -> Model.Config:
    return Model.Config()


def exp001() -> Model.Config:
    cfg = exp000()
    cfg.hidden_size = 512
    cfg.num_layers = 8
    return cfg
```

Or use `@autofig` to auto-generate the Config from `__init__`:

```python
from configgle import autofig
from torch import nn


@autofig
class Model(nn.Module):
    def __init__(self, hidden_size: int = 256, num_layers: int = 4):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers


# Config is auto-generated from __init__ signature
model = Model.Config(hidden_size=512).make()
print(model.hidden_size)  # 512
```

## Features

### Type-safe `make()`

**tl;dr:** Both `ty` and `basedpyright` are first-class supported.
Unfortunately neither is perfect:

| | `ty` | `basedpyright` |
|---|:---:|:---:|
| Bare `Fig` infers parent type | ✅ | ❌ (`Any` fallback) |
| Explicit `Fig["Parent"]` specifies parent type | ✅ | ✅ |
| Inheritance infers parent type | ✅ | ❌ |
| Explicit `Makes["Child"]` narrows inferred inherited parent type | ✅ | ✅ |
| Inherited Config child fields | ✅ (workaround for [#3282](https://github.com/astral-sh/ty/issues/3282)) | ✅ |
| `@autofig` `.Config` access | ✅ (fixed [#143](https://github.com/astral-sh/ty/issues/143)) | ✅ |

**Details:**

When `Config` is defined as a nested class, `MakerMeta.__get__` uses the
descriptor protocol to infer the parent class automatically. The return type
of `__get__` is `Intersection[type[Config], type[Makeable[Parent]]]`, so
`make()` knows the exact return type with zero annotation effort:

```python
class Model:
    class Config(Fig):
        hidden_size: int = 256

    def __init__(self, config: Config):
        self.hidden_size = config.hidden_size


model = Model.Config(hidden_size=512).make()  # inferred as Model
```

Type checkers that support `Intersection` (like `ty`) resolve this fully --
bare `Fig` is all you need. For type checkers that don't yet support
`Intersection` (like `basedpyright`), parameterize with the parent class
name to give the checker the same information explicitly:

```python
class Model:
    class Config(Fig["Model"]):  # explicit type parameter only for basedpyright
        hidden_size: int = 256

    def __init__(self, config: Config):
        self.hidden_size = config.hidden_size


model: Model = Model.Config(hidden_size=512).make()  # returns Model, not object
```

Without `["Model"]`, non-`ty` checkers fall back to `Any` (so attribute access
works without typecheck suppressions).

`ty` gets full inference from `Intersection` -- bare `Fig` and inherited
configs just work. `basedpyright` doesn't support `Intersection` yet, so it
needs explicit `Fig["Parent"]` and `Makes["Child"]` annotations. `ty`
honors class decorator return types ([#143](https://github.com/astral-sh/ty/issues/143),
fixed in 0.0.49), so `@autofig`-decorated classes resolve `.Config` with no
suppression on both checkers. When `Intersection` lands in the
[type spec](https://github.com/python/typing/issues/213), `Makes` becomes
unnecessary and both checkers will infer everything from bare `Fig`.

### Inheritance with `Makes` (only for `basedpyright`)

When a child class inherits a parent's Config, the `make()` return type would
normally be the parent. Use `Makes` to re-bind it (again, only needed for `basedpyright`):

```python
from configgle import Makes


class Animal:
    class Config(Fig["Animal"]):
        name: str = "animal"

    def __init__(self, config: Config):
        self.config = config
        self.name = config.name


class Dog(Animal):
    class Config(Makes["Dog"], Animal.Config):
        breed: str = "mutt"

    def __init__(self, config: Config):
        super().__init__(config)
        self.breed = config.breed


dog: Dog = Dog.Config(name="Rex", breed="labrador").make()  # returns Dog, not Animal
```

`Makes` contributes nothing to the MRO at runtime -- it exists purely for the
type checker (see the [type checker table](#type-safe-make) above). When
[Intersection](https://github.com/python/typing/issues/213) lands, `Makes`
becomes unnecessary.

### Covariant `Makeable` protocol

`Makeable[T]` is a covariant protocol satisfied by any `Fig`, `InlineConfig`,
or custom class exposing `make()`, `finalize()`, `update()`, plus the
`_finalized` and `parent_class` members (`Maker` and `InlineConfig` provide all
five). Because it's covariant, `Makeable[Dog]` is assignable to
`Makeable[Animal]`:

```python
from configgle import Makeable


def train(config: Makeable[Animal]) -> Animal:
    return config.make()


# All valid:
train(Animal.Config())
train(Dog.Config(breed="poodle"))
```

This makes it easy to write functions that accept any config for a class
hierarchy without losing type information.

### Nested config finalization -- pre / super / post

Override `finalize()` to compute derived fields. `super().finalize()` cascades
into the child configs, so it splits the method into a **pre** phase (before
children finalize -- push values down) and a **post** phase (after -- derive
values up):

```python
from configgle import Configurable  # Just an alias to Makeable.
from dataclasses import field


class Encoder:
    class Config(Fig):
        c_in: int = 256
        mlp: Configurable[nn.Module] = field(default_factory=MLP.Config)

        def finalize(self) -> Self:
            self.mlp.c_in = self.c_in  # pre: push down into the child
            self = super().finalize()  # children finalize here
            self.out = self.mlp.out  # post: derive up from the child
            return self
```

Inject into a child **before** `super()` (so it finalizes with the value);
derive from a child **after** (so you read its finalized result). Pushdown is
the common case, so `super()` is usually last -- but it need not be.

`finalize()` mutates in place; the copy that protects the original happens once
at the `make()` / `pprint` boundary (`copy_tree().finalize()`), so a config is
finalized exactly once on a fresh tree (never re-finalized) and the config
passed to `make()` is left untouched.

### `update()` for bulk mutation

Configs support bulk updates from another config or keyword arguments:

```python
cfg = Model.Config(hidden_size=256)
cfg.update(hidden_size=512, num_layers=8)

# Or copy from another config (kwargs take precedence):
cfg.update(other_cfg, num_layers=12)
```

### `InlineConfig` / `PartialConfig`

`InlineConfig` wraps an arbitrary callable and its arguments into a config
object with deferred execution. Use it for classes where all constructor
arguments are known at config time:

```python
from configgle import InlineConfig
import torch.nn as nn

cfg = InlineConfig(nn.Linear, in_features=256, out_features=128, bias=False)
cfg.out_features = 64  # attribute-style access to kwargs
layer = cfg.make()  # calls nn.Linear(in_features=256, out_features=64, bias=False)
y = layer(x)  # use the constructed module
```

`PartialConfig` is shorthand for `InlineConfig(functools.partial, fn, ...)`
-- use it for functions where some arguments aren't known at config time:

```python
from configgle import PartialConfig
import torch.nn.functional as F

cfg = PartialConfig(F.cross_entropy, label_smoothing=0.1)
loss_fn = cfg.make()  # returns functools.partial(F.cross_entropy, label_smoothing=0.1)
loss = loss_fn(
    logits, targets
)  # calls F.cross_entropy(logits, targets, label_smoothing=0.1)
```

Nested configs in args/kwargs are finalized and `make()`-d recursively, so
both compose naturally with `Fig` configs.

### `copy_tree()`

`copy_tree()` is a "semi-deep" copy: nested configs and mutable containers
holding configs are duplicated, while leaf values (primitives, tensors,
loggers) are aliased. `make()` and `pprint` apply it before finalizing so the
source config stays pristine. Reach for it directly to finalize a copy without
touching the source:

```python
finalized = cfg.copy_tree().finalize()  # cfg unchanged
```

### `pprint` / `pformat`

Config-aware pretty printing that hides default values, auto-finalizes before
printing, and scrubs memory addresses:

```python
from configgle import Configurable, Fig, pformat


class MLP:
    class Config(Fig):
        c_in: int = 256
        c_out: int = 256
        num_layers: int = 2
        dropout: float = 0.1
        use_bias: bool = True

    def __init__(self, config: Config): ...


class Model:
    class Config(Fig):
        hidden_size: int = 256
        num_layers: int = 4
        mlp: Configurable[nn.Module] = field(default_factory=MLP.Config)
        output_mlp: Configurable[nn.Module] = field(default_factory=MLP.Config)

    def __init__(self, config: Config): ...


def exp001():
    cfg = Model.Config()
    cfg.hidden_size = 512
    cfg.num_layers = 12
    cfg.mlp.c_in = 512
    cfg.mlp.c_out = 1024
    cfg.mlp.num_layers = 4
    cfg.mlp.dropout = 0.2
    cfg.mlp.use_bias = False
    cfg.output_mlp.c_in = 1024
    cfg.output_mlp.c_out = 256
    cfg.output_mlp.dropout = 0.3
    return cfg


print(pformat(exp001(), continuation_pipe=0))
# Model.Config(
#    hidden_size=512,
#    num_layers=12,
#    mlp=MLP.Config(
#    │       c_in=512,
#    │       c_out=1_024,
#    │       num_layers=4,
#    │       dropout=0.2,
#    │       use_bias=False
#    ),
#    output_mlp=MLP.Config(c_in=1_024, dropout=0.3)
# )
```

Default values are hidden, continuation pipes show where nested blocks belong,
large numbers get underscores (`1_024`), and short sub-configs collapse onto
one line. `pformat` and `pprint` are also available as methods on any `Fig` config:

```python
cfg = exp001()
cfg.pprint()  # prints to stdout
s = cfg.pformat()  # returns string
```

### CLI overrides

`apply_overrides` edits a config from `PATH=VALUE` strings. Dotted paths reach
into nested configs, every hop is checked against the node's declared fields
(so a typo raises instead of silently creating an attribute), and the value is
cast to the field's declared type:

```python
from configgle import apply_overrides

cfg = Model.Config()
apply_overrides(cfg, ["hidden_size=512", "mlp.dropout=0.2"])
```

`configgle/launch.py` wires that to argparse, so any factory function returning
a config is runnable as-is:

```python
# myproject/experiments.py
def baseline() -> Makeable[Trainer]:
    return Trainer.Config()
```

```sh
python -m configgle myproject.experiments.baseline --override mlp.dropout=0.2
```

The launcher is deliberately small -- it exists to make `--override` usable out
of the box and to show the pattern. A real project usually wants its own entry
point (hardware logging, distributed setup, run naming); build it on
`resolve_config` and `apply_overrides` rather than copying the file.

### `Dataclass` base

`Dataclass` provides the auto-dataclass metaclass (with the same opinionated
defaults as `Fig`: `kw_only=True`, `slots=True`, etc.) but without `Maker` or
`make()`. Use it for plain data objects that don't need the factory pattern.

### `@autofig` for zero-boilerplate configs

When you don't need a hand-written Config, `@autofig` generates one from
`__init__` (see [Example](#example) above).

### Pickling and cloudpickle

Configs are fully compatible with `pickle` and `cloudpickle`, including the
parent class reference. This is important for distributed workflows (e.g.,
sending configs across processes):

```python
import cloudpickle, pickle

cfg = Model.Config(hidden_size=512)
cfg_ = pickle.loads(cloudpickle.dumps(cfg))
model = cfg_.make()  # parent_class is preserved
```

## Comparison

| | [configgle](https://github.com/rekursiv-ai/configgle) | [Hydra](https://github.com/facebookresearch/hydra) | [Sacred](https://github.com/IDSIA/sacred) | [OmegaConf](https://github.com/omry/omegaconf) | [Gin](https://github.com/google/gin-config) | [ml_collections](https://github.com/google/ml_collections) | [Fiddle](https://github.com/google/fiddle) | [Confugue](https://github.com/cifkao/confugue) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Python-based | ✅ | 🟡 | 🟡 | 🟡 | ❌ | ✅ | ✅ | 🟡 |
| YAML-based | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| CLI overrides | ✅ | ✅ | ✅ | 🟡 | 🟡 | ✅ | ✅ | ❌ |
| Sweeps / multirun | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | 🟡 | ❌ |
| Typed `make()`/`build()` return | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Derived fields | ✅ | 🟡 | 🟡 | 🟡 | ❌ | 🟡 | ❌ | ❌ |
| Config from signature | ✅ | 🟡 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| JSON round-trip (typed) | ✅ | 🟡 | 🟡 | 🟡 | ❌ | 🟡 | ✅ | ❌ |
| `pickle`/`cloudpickle` | ✅ | 🟡 | 🟡 | ✅ | 🟡 | 🟡 | ✅ | 🟡 |
| Active | ✅ | ✅ | 🟡 | ✅ | 🟡 | 🟡 | 🟡 | ❌ |

✅ = yes, 🟡 = partial, ❌ = no. Corrections welcome --
[open a PR](https://github.com/rekursiv-ai/configgle/pulls).

Row notes, since several are easy to read the wrong way:

- **Python-based / YAML-based** are independent axes, not opposites. Gin is
  neither -- it has its own `.gin` DSL. configgle is Python-only by design, so
  it loses the YAML row outright: if your collaborators edit configs without
  touching Python, that is a real reason to pick Hydra or OmegaConf instead.
- **Sweeps / multirun** means launching many runs from one command. Hydra's
  `--multirun` is the only first-class implementation; configgle has none (write
  a loop over config functions). Fiddle's `DEFINE_fiddle_sweep` is on `main`
  only, absent from the latest PyPI release, and emits configs without running
  them.
- **Derived fields** means computing one field from others. configgle's
  `finalize()` is a user-overridable hook that cascades through child configs;
  the 🟡 libraries re-run `__post_init__` (Hydra, OmegaConf) or re-execute config
  scopes (Sacred) at a conversion boundary, and ml_collections has lazy
  `FieldReference`.
- **JSON round-trip (typed)** means dump to JSON *and* load back into live typed
  objects. Every 🟡 reloads to an untyped dict: ml_collections has `to_json()`
  but no `from_json`, and OmegaConf's reload yields
  `OmegaConf.get_type(...) == dict`.
- **Active** is measured from the last PyPI release, not repo activity. 🟡 marks
  a library whose repo still moves but whose last release is aging (Gin 0.5.0,
  2021-11-03; Fiddle 0.3.0, 2024-04-09; Sacred 0.8.7, 2024-11-26; ml_collections
  1.1.0, 2025-04-17). Confugue's last release was 2020-04-22 and its last commit
  2021-09-13.

<details>
<summary><b>How each library works</b></summary>

**[Hydra](https://github.com/facebookresearch/hydra)** (Meta) --
YAML-centric with optional "structured configs" (Python dataclasses registered
in a `ConfigStore`). Instantiation uses `hydra.utils.instantiate()`, which
resolves a `_target_` field -- typically a string import path, though a class
object is also accepted -- and returns `Any`. Composition is done via defaults
lists (usually YAML, optionally a `defaults` field on a dataclass), not class
inheritance; dataclass inheritance works at the schema level. `configen` is an
experimental code-generation tool (latest release v0.9.0.dev8) that produces
structured configs from class signatures. Its `--multirun` sweeper is the most
complete in this table.

**[Sacred](https://github.com/IDSIA/sacred)** --
Experiment management framework. Config is defined via `@ex.config` scopes
(local variables become config entries) or loaded from YAML/JSON/pickle files,
and overridden on the command line with `with 'a.b=5'`. Sacred auto-*injects*
config values into captured functions by parameter name (dependency injection),
but does not auto-*generate* configs from function signatures. Reuse is by
composition -- ingredients nest, and stacked config scopes override a
reusable ingredient's defaults -- rather than class inheritance. No typed
factory methods; `Experiment` objects are not picklable, though config *files*
may be pickles.

**[OmegaConf](https://github.com/omry/omegaconf)** --
YAML-native configuration with a "structured config" mode that accepts
`@dataclass` schemas. Configs are `DictConfig` proxy objects at runtime, not
dataclass instances; `OmegaConf.to_object()` converts them back into real
instances (re-running `__post_init__` recursively as it goes). Supports
dataclass inheritance for schema definition. Good pickle support
(`__getstate__`/`__setstate__`). `to_object()` acts as a factory but is typed
`Any`, so callers lose static types. `OmegaConf.from_cli()` parses a dotlist
but leaves the merge to you. No auto-generation, no protocols.

**[Gin](https://github.com/google/gin-config)** (Google) --
Global string-based registry. You decorate functions with `@gin.configurable`
and bind parameters via `.gin` files or `gin.bind_parameter('fn.param', val)`.
There are no config objects -- parameter values live in a global dict keyed by
`(scope, selector)`. No typed returns, and no config-object inheritance (though
`.gin` files compose via `include`, and scoped bindings inherit from the root
scope). The docs still state "Gin-configurable functions are not pickleable,"
but as of 2021 Gin wraps the metaclass `__call__` so that *instances* of
configurable classes pickle fine; a community PR proposing `__reduce__` was
closed unmerged.

**[ml_collections](https://github.com/google/ml_collections)** (Google) --
Dict-like `ConfigDict` with dot-access, type-checking on mutation, and
`FieldReference` for lazy cross-references between values. Config files are
Python, not YAML (the library itself depends on PyYAML for printing).
`config_flags` gives `--config.foo.bar=3e-4` overrides for free. No factory
method or typed instantiation. Pickle works for plain configs, but
`FieldReference` operations that build lambdas internally (`.identity()` --
used by `get_oneway_ref()` -- and the `.to_int()`/`.to_float()`/`.to_str()`
casts) fail with standard pickle; cloudpickle handles them.

**[Fiddle](https://github.com/google/fiddle)** (Google) --
Python-first. You build config graphs with `fdl.Config[MyClass]` objects and
call `fdl.build()` to instantiate them. `build(Config[T]) -> T` is typed via
`@overload`. Config modification is functional (`fdl.copy_with`) -- you don't
subclass a config to override values. `@auto_config` rewrites a factory
function's AST to produce a config graph automatically. Full
pickle/cloudpickle support, and `serialization.dump_json`/`load_json` round-trip
a config graph faithfully (though that module lives under `_src.experimental`).

**[Confugue](https://github.com/cifkao/confugue)** --
YAML-based hierarchical configuration. The `configure()` method instantiates
objects from YAML dicts, with the class overridden via a `class:` key whose
value uses PyYAML's `!!python/name:` tag. Returns `Any`. Partial config
inheritance via YAML merge keys (`<<: *base`). No CLI, no auto-generation, no
protocols. Pickling is undocumented and untested -- configured instances do
pickle, but `bind()` results do not. Unmaintained: last release 2020-04-22,
last commit 2021-09-13.

</details>

## Citing

If you find our work useful, please consider citing:

```bibtex
@misc{rekursivai2026configgle,
      title={Configgle - Type-safe hierarchical experiment configuration using pure Python dataclass factories and dependency injection.},
      author={Joshua V. Dillon},
      year={2026},
      howpublished={Github},
      url={https://github.com/rekursiv-ai/configgle},
}
```

## License

Apache License 2.0
