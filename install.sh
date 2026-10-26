#!/bin/sh
set -eu
task_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$task_dir/ilha/scripts/install_shell.py" --user "$@"
