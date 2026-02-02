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

## License

Apache License 2.0
