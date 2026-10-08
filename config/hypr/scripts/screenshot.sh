#!/usr/bin/env bash
# Screenshots via grim/slurp. The old inline binds computed $(date) twice, so
# the file was written under one name and wl-copy read another.
set -euo pipefail

dir="${XDG_PICTURES_DIR:-$HOME/Pictures}/Screenshots"
mkdir -p "$dir"
file="$dir/$(date +%Y-%m-%d_%H-%M-%S).png"

preview="${XDG_RUNTIME_DIR:-/tmp}/hypr-screenshot.png"
notify() {
  command -v notify-send >/dev/null || return 0
  local title=$1 body=${2-} icon=${3:-$preview}
  if [[ -f $icon ]]; then
    notify-send -a Screenshot -i "$icon" "$title" "$body"
  else
    notify-send -a Screenshot "$title" "$body"
  fi
}

# Region in its own assignment, not inline in grim's args: a cancelled slurp
# (ESC) exits non-zero, and `grim -g "$(slurp)"` swallowed that — grim then ran
# with an empty geometry and the empty output still went to wl-copy, wiping the
# clipboard. As an assignment, `set -e` aborts here instead.
region() { geom=$(slurp); }

copy_png() { wl-copy --type image/png < "$1"; }

# --type: don't let wl-copy guess the mime for binary PNG data.
case "${1:-region}" in
  region)  region; grim -g "$geom" "$preview" && copy_png "$preview" && notify "Copied to clipboard" ;;
  screen)  grim "$preview" && copy_png "$preview" && notify "Screen copied to clipboard" ;;
  save)    region; grim -g "$geom" "$file" && copy_png "$file" && notify "Saved" "$file" "$file" ;;
  edit)    region; grim -g "$geom" - | swappy -f - ;;
  *)       echo "usage: ${0##*/} region|screen|save|edit" >&2; exit 2 ;;
esac
