# Release Process

Releases are tag-driven.

## Preflight

```bash
python -m unittest discover tests
python scripts/secret_scan.py
python -m build
python -m twine check dist/*
```

## Tag

```bash
git tag v0.1.0
git push origin v0.1.0
```

The release workflow builds the package, publishes to PyPI with trusted publishing, and creates a GitHub Release.

Before first PyPI release, configure PyPI trusted publishing for:

```text
owner: EricEEEEEEE
repository: macro-regime-kit
workflow: release.yml
environment: pypi
```

