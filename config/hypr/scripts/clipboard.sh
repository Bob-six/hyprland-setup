#!/usr/bin/env bash
# Clipboard history picker. cliphist records every copy (see autostart.conf);
# this reads it back and puts the pick on the clipboard.
# Wipe history with: cliphist wipe
set -euo pipefail
cliphist list | rofi -dmenu -i -replace -p "Clipboard" | cliphist decode | wl-copy
