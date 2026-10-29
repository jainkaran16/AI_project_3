#!/bin/zsh
# Open the supplied keyboard demo from this folder or a Finder double-click.
cd -- "$(dirname -- "$0")" || exit 1
exec python3 play_gui.py "$@"
