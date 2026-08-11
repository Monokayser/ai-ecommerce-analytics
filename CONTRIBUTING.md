# Contributing

Thank you for improving the project.

1. Fork the repository and create a focused branch from `main`.
2. Install `requirements-dev.txt` in a Python 3.11 virtual environment.
3. Keep business logic under `src/`; keep `app.py` limited to initialization and routing.
4. Add or update tests for every behavior change, especially query validation and exports.
5. Run `python -m pytest -q` and verify that no secrets, private datasets, or generated reports are staged.
6. Open a pull request explaining the user-visible change, verification performed, and security implications.

Use descriptive commit messages such as `feat: add cohort comparison` or `fix: reject external DuckDB scans`. Never manufacture development history or benchmark results.
