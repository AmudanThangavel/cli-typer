Contributing to CLI Typer

Thanks for your interest in contributing! This project welcomes issues and pull requests.

How to get started

- Run locally: `python3 cli_typer.py`
- Non-interactive check: `python3 cli_typer.py --check`
- Run tests/lints in CI style:
  - `pip install ruff`
  - `ruff check . --select=E9,F63,F7,F82`

Submitting changes

- Open an issue first for larger changes to align on approach.
- Keep PRs focused and include a short description of the change and rationale.
- Match the existing code style and keep dependencies minimal.

Development tips

- The TUI uses Python `curses`. Test in a real terminal (TTY).
- Windows requires `windows-curses`.
- Use `--seed` to reproduce word generation during dev.

Release process

- See RELEASING.md for building and publishing to TestPyPI/PyPI.

Code of Conduct

- This project follows the Contributor Covenant. See CODE_OF_CONDUCT.md.

