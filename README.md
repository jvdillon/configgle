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
      title={Configgle - Hierarchical experiment configuration and dependency injection using pure Python dataclass factories.},
      author={Joshua V. Dillon},
      year={2026},
      howpublished={Github},
      url={https://github.com/jvdillon/configgle},
}
```

## License

Apache License 2.0
