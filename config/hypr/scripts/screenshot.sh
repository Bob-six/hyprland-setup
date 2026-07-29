#!/usr/bin/env bash
# Screenshots via grim/slurp. The old inline binds computed $(date) twice, so
# the file was written under one name and wl-copy read another.
set -euo pipefail

dir="${XDG_PICTURES_DIR:-$HOME/Pictures}/Screenshots"
mkdir -p "$dir"
file="$dir/$(date +%Y-%m-%d_%H-%M-%S).png"

notify() { command -v notify-send >/dev/null && notify-send -a Screenshot "$1" "${2-}"; }

case "${1:-region}" in
  region)  grim -g "$(slurp)" - | wl-copy && notify "Copied to clipboard" ;;
  screen)  grim - | wl-copy && notify "Screen copied to clipboard" ;;
  save)    grim -g "$(slurp)" "$file" && wl-copy < "$file" && notify "Saved" "$file" ;;
  edit)    grim -g "$(slurp)" - | swappy -f - ;;
  *)       echo "usage: ${0##*/} region|screen|save|edit" >&2; exit 2 ;;
esac
