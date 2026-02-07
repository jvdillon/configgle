# configgle🤭
Tools for making configurable Python classes for A/B experiements.

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

## References

Why another config library? There are great options out there, but they either
focus more on YAML or wrapper objects. The goal with configgle is a UX that's
just simple Python--standard dataclasses, hierarchical, and class-local. No
external files, no new syntax to learn.

The following libraries span these ideas but none wholly combine them:

- [Hydra](https://github.com/facebookresearch/hydra) - Framework for elegantly configuring complex applications
- [OmegaConf](https://github.com/omry/omegaconf) - Flexible hierarchical configuration system
- [Confugue](https://github.com/cifkao/confugue) - Hierarchical configuration with YAML-based object instantiation (most similar to configgle, but uses YAML rather than pure Python)
- [Fiddle](https://github.com/google/fiddle) - Python-first configuration library for ML
- [Gin Config](https://github.com/google/gin-config) - Lightweight configuration framework for Python
- [Sacred](https://github.com/IDSIA/sacred) - Tool to configure, organize, log and reproduce experiments
- [ml_collections](https://github.com/google/ml_collections) - Python collections designed for ML use cases

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
