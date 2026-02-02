# Releasing to PyPI

1. Update version in `pyproject.toml`

2. Build and upload:
   ```bash
   uv sync --group publish
   uv run python -m build
   uv run twine upload dist/*
   ```

3. Clean up build artifacts:
   ```bash
   rm -rf dist/ *.egg-info/
   ```
