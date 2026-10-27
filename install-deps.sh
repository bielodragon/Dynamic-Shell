#!/bin/sh
set -eu
task_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3 >/dev/null 2>&1; then
    echo 'Instale primeiro Python 3: sudo pacman -S --needed python' >&2
    exit 1
fi
exec python3 "$task_dir/ilha/scripts/install_dependencies.py" "$@"
