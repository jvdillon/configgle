# Releasing to PyPI

1. Increment version in `pyproject.toml` and `git push` it.

2. Build and upload:
   ```bash
   uv sync --group publish && uv run python -m build && uv run twine upload dist/*
   ```

3. Create GitHub release:
   ```bash
   gh release create v0.1.0 --title "v0.1.0" --notes "Initial release"
   ```

4. Clean up build artifacts:
   ```bash
   rm -rf dist/
   ```
