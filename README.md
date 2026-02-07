# configgle🤭
Hierarchical configuration using pure Python dataclasses, with typed factory
methods, covariant protocols, and full inheritance support.

## Installation

```bash
python -m pip install configgle
```

## Example

```python
from configgle import Fig

class Model:
    class Config(Fig["Model"]):
        hidden_size: int = 256
        num_layers: int = 4

    def __init__(self, config: Config):
        self.config = config

# Create and modify config
config = Model.Config(hidden_size=512)

# Instantiate the parent class
model = config.make()
print(model.config.hidden_size)  # 512
```

Or use `@autofig` to auto-generate the Config from `__init__`:

```python
from configgle import autofig

@autofig
class Model:
    def __init__(self, hidden_size: int = 256, num_layers: int = 4):
        self.hidden_size = hidden_size
        self.num_layers = num_layers

# Config is auto-generated from __init__ signature
model = Model.Config(hidden_size=512).make()
print(model.hidden_size)  # 512
```

## Features

### Type-safe `make()`

`Fig` tracks the parent class automatically. You can use bare `Fig` and
everything works with no type warnings -- the type parameter defaults to `Any`:

```python
class Model:
    class Config(Fig):
        hidden_size: int = 256

    def __init__(self, config: Config):
        self.hidden_size = config.hidden_size

model = Model.Config(hidden_size=512).make()
```

For tighter checking, parameterize with the parent class name and `make()`
returns the exact type:

```python
class Model:
    class Config(Fig["Model"]):
        hidden_size: int = 256

    def __init__(self, config: Config):
        self.hidden_size = config.hidden_size

model: Model = Model.Config(hidden_size=512).make()  # returns Model, not object
```

### Inheritance with `Makes`

When a child class inherits a parent's Config, the `make()` return type would
normally be the parent. Use `Makes` to re-bind it:

```python
class Animal:
    class Config(Fig["Animal"]):
        name: str = "animal"

    def __init__(self, config: Config):
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
type checker. It's a workaround for Python's lack of an `Intersection` type:
`MakerMeta.__get__` already narrows `Dog.Config` to
`type[Config] & type[Makeable[Dog]]` at runtime, but there's no way to express
that statically today. When
[Intersection](https://github.com/python/typing/issues/213) lands, `Makes`
will become unnecessary -- configgle is already forward-compatible with that
change.

### Covariant `Makeable` protocol

`Makeable[T]` is a covariant protocol satisfied by any `Fig`, `InlineConfig`,
or custom class with `make()`, `finalize()`, and `update()`. Because it's
covariant, `Makeable[Dog]` is assignable to `Makeable[Animal]`:

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

### Nested config finalization

Override `finalize()` to compute derived fields before instantiation. Nested
configs are finalized recursively:

```python
class Encoder:
    class Config(Fig["Encoder"]):
        c_in: int = 256
        mlp: MLP.Config = field(default_factory=MLP.Config)

        def finalize(self) -> Self:
            self = super().finalize()
            self.mlp.c_in = self.c_in  # propagate dimensions
            return self
```

### `update()` for bulk mutation

Configs support bulk updates from another config, a dict, or keyword arguments:

```python
cfg = Model.Config(hidden_size=256)
cfg.update(hidden_size=512, num_layers=8)

# Or copy from another config (kwargs take precedence):
cfg.update(other_cfg, num_layers=12)
```

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

| | [configgle](https://github.com/jvdillon/configgle) | [Hydra](https://github.com/facebookresearch/hydra) | [Sacred](https://github.com/IDSIA/sacred) | [OmegaConf](https://github.com/omry/omegaconf) | [Gin](https://github.com/google/gin-config) | [ml_collections](https://github.com/google/ml_collections) | [Fiddle](https://github.com/google/fiddle) | [Confugue](https://github.com/cifkao/confugue) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Pure Python (no YAML/strings) | ✅ | ❌ | ❌ | 🟡 | ❌ | ✅ | ✅ | ❌ |
| Typed `make()`/`build()` return | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Config inheritance | ✅ | 🟡 | ❌ | 🟡 | ❌ | ❌ | ❌ | 🟡 |
| Covariant protocol | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Nested finalization | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `pickle`/`cloudpickle` | ✅ | 🟡 | ❌ | ✅ | ❌ | 🟡 | ✅ | ❌ |
| Auto-generated configs | ✅ | 🟡 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| GitHub stars | -- | 10.2k | 4.4k | 2.3k | 2.1k | 1.0k | 374 | 21 |

✅ = yes, 🟡 = partial, ❌ = no. Corrections welcome --
[open a PR](https://github.com/jvdillon/configgle/pulls).

### How each library works

**[Hydra](https://github.com/facebookresearch/hydra)** (Meta) --
YAML-centric with optional "structured configs" (Python dataclasses registered
in a `ConfigStore`). Instantiation uses `hydra.utils.instantiate()`, which
resolves a string `_target_` field to an import path -- the return type is
`Any`. Config composition is done via YAML defaults lists, not class
inheritance. Dataclass inheritance works at the schema level. `configen` is
an experimental code-generation tool (v0.9.0.dev8) that produces structured
configs from class signatures. Configs survive pickle trivially since
`_target_` is a string, not a class reference.

**[Sacred](https://github.com/IDSIA/sacred)** --
Experiment management framework. Config is defined via `@ex.config` scopes
(local variables become config entries) or loaded from YAML/JSON files. Sacred
auto-*injects* config values into captured functions by parameter name
(dependency injection), but does not auto-*generate* configs from function
signatures. No typed factory methods, no config inheritance, no pickle
support for the experiment/config machinery.

**[OmegaConf](https://github.com/omry/omegaconf)** --
YAML-native configuration with a "structured config" mode that accepts
`@dataclass` schemas. Configs are always wrapped in `DictConfig` proxy objects
at runtime (not actual dataclass instances). Supports dataclass inheritance
for schema definition. Good pickle support (`__getstate__`/`__setstate__`).
No factory method (`to_object()` returns `Any`), no auto-generation, no
protocols.

**[Gin](https://github.com/google/gin-config)** (Google) --
Global string-based registry. You decorate functions with `@gin.configurable`
and bind parameters via `.gin` files or `gin.bind_parameter('fn.param', val)`.
There are no config objects -- parameter values live in a global dict keyed by
dotted strings. No typed returns, no config inheritance. The docs state
"gin-configurable functions are not pickleable," though a 2020 PR added
`__reduce__` methods that improve support.

**[ml_collections](https://github.com/google/ml_collections)** (Google) --
Dict-like `ConfigDict` with dot-access, type-checking on mutation, and
`FieldReference` for lazy cross-references between values. Pure Python, no
YAML. No factory method or typed instantiation. Pickle works for plain configs,
but `FieldReference` operations that use lambdas internally (`.identity()`,
`.to_int()`) fail with standard pickle (cloudpickle handles them).

**[Fiddle](https://github.com/google/fiddle)** (Google) --
Python-first. You build config graphs with `fdl.Config[MyClass]` objects and
call `fdl.build()` to instantiate them. `build(Config[T]) -> T` is typed via
`@overload`. Config modification is functional (`fdl.copy_with`), not
inheritance-based -- there are no config subclasses. `@auto_config` rewrites a
factory function's AST to produce a config graph automatically. Full
pickle/cloudpickle support.

**[Confugue](https://github.com/cifkao/confugue)** --
YAML-based hierarchical configuration. The `configure()` method instantiates
objects from YAML dicts, with the class specified via a `!type` YAML tag.
Returns `Any`. Partial config inheritance via YAML merge keys (`<<: *base`).
No pickle support, no auto-generation, no protocols.

## Citing

If you find our work useful, please consider citing:

```bibtex
@misc{dillon2026configgle,
      title={Configgle - Hierarchical experiment configuration using pure Python dataclass factories and dependency injection.},
      author={Joshua V. Dillon},
      year={2026},
      howpublished={Github},
      url={https://github.com/jvdillon/configgle},
}
```

## License

Apache License 2.0
