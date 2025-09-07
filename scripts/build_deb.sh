#!/usr/bin/env bash
set -euo pipefail

if ! command -v debuild >/dev/null 2>&1; then
  echo "debuild is not installed. On Ubuntu/Debian:"
  echo "  sudo apt update && sudo apt install -y devscripts debhelper dh-python python3-all python3-setuptools"
  exit 1
fi

debuild -us -uc
echo "\nBuilt .deb(s) in the parent directory (..)."

