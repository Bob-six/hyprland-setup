#!/usr/bin/env bash
# Searchable keybind cheat sheet.
#
# Reads the binds Hyprland actually has loaded (`hyprctl binds -j`) instead of
# parsing conf/binds.lua, so it can't go stale: every bind declared with a
# `description` shows up here. (The old ML4W keybindings.sh parsed a
# keybindings.conf that didn't exist.)
#
# Run with --test to check the modmask decoding without opening rofi.
set -euo pipefail

# modmask is a bitfield: 1 SHIFT, 4 CTRL, 8 ALT, 64 SUPER
render() {
  jq -r '
    def mods(m):
      [ if m % 128 >= 64 then "SUPER" else empty end,
        if m % 16  >= 8  then "ALT"   else empty end,
        if m % 8   >= 4  then "CTRL"  else empty end,
        if m % 2   >= 1  then "SHIFT" else empty end ] | join(" + ");

    map(select(.description != ""))
    | unique_by(.modmask, .key, .description)
    | map("\((mods(.modmask) + " + " + .key) | ltrimstr(" + "))\t\(.description)")
    | .[]
  '
}

if [[ ${1-} == --test ]]; then
  got=$(render <<'JSON' | tr '\t' '|'
[ {"modmask":64,"key":"Q","description":"Close window"},
  {"modmask":65,"key":"M","description":"Exit Hyprland"},
  {"modmask":68,"key":"B","description":"Hide/show waybar"},
  {"modmask":73,"key":"left","description":"Move workspace to left monitor"},
  {"modmask":0,"key":"Print","description":"Screenshot"},
  {"modmask":64,"key":"X","description":""} ]
JSON
)
  # unique_by sorts by (modmask, key), hence this order; the final sort is done
  # by `column | sort` in the real path.
  want='Print|Screenshot
SUPER + Q|Close window
SUPER + SHIFT + M|Exit Hyprland
SUPER + CTRL + B|Hide/show waybar
SUPER + ALT + SHIFT + left|Move workspace to left monitor'
  [[ $got == "$want" ]] || { printf 'FAIL\n--- got ---\n%s\n--- want ---\n%s\n' "$got" "$want" >&2; exit 1; }
  echo "ok"
  exit 0
fi

hyprctl binds -j | render | column -t -s $'\t' | sort -k1 \
  | rofi -dmenu -i -replace -p "Keybinds" -theme-str 'listview { columns: 1; lines: 16; }' \
  >/dev/null
