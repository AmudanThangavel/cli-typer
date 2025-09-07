PYTHON ?= python3
PKG = cli-typer

.PHONY: help build wheel sdist clean deb deb-clean check

help:
	@echo "Targets:"
	@echo "  build      - build sdist+wheel"
	@echo "  check      - run non-interactive self-check"
	@echo "  deb        - build Debian package (.deb)"
	@echo "  deb-clean  - clean Debian build artifacts"
	@echo "  clean      - clean Python build artifacts"

build:
	$(PYTHON) -m pip install --upgrade build >/dev/null 2>&1 || true
	$(PYTHON) -m build

wheel: build

sdist: build

check:
	$(PYTHON) cli_typer.py --check

deb:
	debuild -us -uc

deb-clean:
	rm -rf ../$(PKG)_* *.build *.changes *.upload *.dsc *.tar.* *.deb

clean: deb-clean
	rm -rf build dist *.egg-info __pycache__

