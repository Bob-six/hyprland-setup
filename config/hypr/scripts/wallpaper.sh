#!/usr/bin/env bash
# Pick a wallpaper for every monitor. hyprpaper runs with ipc on, so this
# applies live — the old reload-hyprpaper.sh killed and respawned the daemon.
set -euo pipefail

dir="${XDG_PICTURES_DIR:-$HOME/Pictures}/wallpapers"
conf="$HOME/.config/hypr/hyprpaper.conf"
[ -d "$dir" ] || { notify-send "No such directory: $dir"; exit 1; }

pick=$(find "$dir" -maxdepth 1 -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -printf '%f\n' \
        | sort | rofi -dmenu -i -replace -p "Wallpaper")
[ -z "$pick" ] && exit 0

hyprctl hyprpaper preload "$dir/$pick"
hyprctl hyprpaper wallpaper ",$dir/$pick"
hyprctl hyprpaper unload unused

# Persist it: rewrite every wallpapers/<file> reference (preload + path).
# Matches whether the config spells the dir with ~ or absolutely.
sed -i -E "s|(wallpapers/)[^ ]+|\1${pick}|g" "$conf"
