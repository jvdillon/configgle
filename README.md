# configgle 🤭
Tools for making configurable Python classes for A/B experiements.

## Installation

```bash
python -m pip install configgle
```

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
config = Model.Config(hidden_size=512)

# Instantiate the parent class
model = config.setup()
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
model = Model.Config(hidden_size=512).setup()
print(model.hidden_size)  # 512
```

## References

configgle differs from these libraries by keeping configuration purely in Python with no external files or DSLs--the config class lives inside the class it configures and doubles as its factory.

Related configuration and experiment management libraries:

- [Fiddle](https://github.com/google/fiddle) - Python-first configuration library for ML
- [Gin Config](https://github.com/google/gin-config) - Lightweight configuration framework for Python
- [Sacred](https://github.com/IDSIA/sacred) - Tool to configure, organize, log and reproduce experiments
- [Hydra](https://github.com/facebookresearch/hydra) - Framework for elegantly configuring complex applications
- [ml_collections](https://github.com/google/ml_collections) - Python collections designed for ML use cases
- [OmegaConf](https://github.com/omry/omegaconf) - Flexible hierarchical configuration system

## License

Apache License 2.0
