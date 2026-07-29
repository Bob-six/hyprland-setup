#!/usr/bin/env bash
# Never stack lock screens — if hyprlock already runs, do nothing.
pidof hyprlock >/dev/null && exit 0

# Force every keyboard to layout 0 (us) before locking, so the password types
# in english even if the ir layout was active.
hyprctl devices -j 2>/dev/null \
  | jq -r '.keyboards[].name' \
  | while read -r kb; do
      hyprctl switchxkblayout "$kb" 0 >/dev/null
    done
exec hyprlock
