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

## License

Apache License 2.0
