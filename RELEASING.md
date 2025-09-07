Releasing cli-typer to PyPI

This guide covers preparing a release, building artifacts, testing on TestPyPI, tagging, and publishing to PyPI. It also includes optional GitHub Actions automation notes.

Prerequisites

- Python 3.8+
- A PyPI account (and optionally a TestPyPI account)
- Tools: `pip install --upgrade build twine`

Versioning

- Use semantic versioning: MAJOR.MINOR.PATCH (e.g., 0.1.0)
- Update the version in `pyproject.toml` under `[project] version = "X.Y.Z"`

1) Prep the release

- Ensure CI is green on main.
- Update `README.md` and any docs as needed.
- Bump `[project].version` in `pyproject.toml` (e.g., from 0.1.0 -> 0.2.0).

2) Clean old build artifacts

```
rm -rf dist build *.egg-info
```

3) Build sdist + wheel

```
python -m build
```

This creates `dist/cli_typer-X.Y.Z.tar.gz` and `dist/cli_typer-X.Y.Z-py3-none-any.whl`.

4) Check the artifacts

```
twine check dist/*
```

5) Test upload to TestPyPI (recommended)

- Create a TestPyPI token in your TestPyPI account (Scoped to the project name once created on first upload).
- Upload:

```
twine upload -r testpypi dist/*
```

6) Test install from TestPyPI

Use a fresh virtual environment.

```
python -m venv .venv-test
source .venv-test/bin/activate  # on Windows: .venv-test\Scripts\activate
pip install --upgrade pip
# Because dependencies may be on PyPI proper, include the main index as extra
pip install -i https://test.pypi.org/simple --extra-index-url https://pypi.org/simple cli-typer

# Sanity check the console script (non-interactive self-check)
cli-typer --check
# Or via module
python -m cli_typer --check
```

7) Publish to PyPI

- Create a PyPI token in your PyPI account (Project-scoped is recommended once the project exists).
- Upload the same artifacts:

```
twine upload dist/*
```

8) Tag and push the release

```
git tag -a vX.Y.Z -m "Release X.Y.Z"
git push origin vX.Y.Z
```

Optional: GitHub Actions automation

- Secrets to set in your repo:
  - `PYPI_API_TOKEN` — your PyPI token (format: `pypi-...`)
  - `TEST_PYPI_API_TOKEN` — your TestPyPI token (optional, if you want to auto-publish to TestPyPI)

- Example publish workflow (manual trigger) using `pypa/gh-action-pypi-publish`:

```
name: Publish

on:
  workflow_dispatch:

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -m pip install --upgrade pip build
      - run: python -m build

      # Optional: TestPyPI first
      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@v1.8.14
        with:
          password: ${{ secrets.TEST_PYPI_API_TOKEN }}
          repository-url: https://test.pypi.org/legacy/
        if: ${{ secrets.TEST_PYPI_API_TOKEN != '' }}

      # PyPI
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@v1.8.14
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

Notes

- Windows support is provided via a conditional dependency on `windows-curses`.
- The console entry point is `cli-typer`, mapped to `cli_typer:main` in `pyproject.toml`.
- For small releases, you can test locally by installing the wheel:

```
python -m venv .venv-local
source .venv-local/bin/activate
pip install dist/cli_typer-*.whl
cli-typer --check
```

Troubleshooting

- 401 Unauthorized on upload: ensure you’re using the correct token and repo URL (TestPyPI vs PyPI).
- File already exists: increment the version in `pyproject.toml` and rebuild.
- Console script not found after install: ensure `[project.scripts]` is present in `pyproject.toml` and that you installed the built wheel/sdist, not running from source accidentally.

