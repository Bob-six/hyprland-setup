#!/usr/bin/env bash
# Volume / brightness / mic OSD via dunst progress bars.
# Replaces the previous silent wpctl/brightnessctl binds.
set -euo pipefail

id_volume=91190
id_bright=91191
id_mic=91192
icons=/usr/share/icons/Papirus-Dark/48x48/status

notify() {
  local id=$1 icon=$2 title=$3 body=$4 value=$5
  (( value > 100 )) && value=100
  (( value < 0 )) && value=0
  dunstify -a osd -u low -r "$id" -i "$icon" \
    -h string:x-dunst-stack-tag:osd \
    -h int:value:"$value" \
    "$title" "$body"
}

pct_from_wpctl() {
  # "Volume: 0.70" or "Volume: 0.70 [MUTED]"
  awk '{ printf "%d", $2 * 100 }' <<<"$1"
}

volume() {
  case ${1:-} in
    up)   wpctl set-volume -l 1.4 @DEFAULT_AUDIO_SINK@ 5%+ ;;
    down) wpctl set-volume -l 1.4 @DEFAULT_AUDIO_SINK@ 5%- ;;
    mute) wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle ;;
    *)    echo "usage: ${0##*/} volume up|down|mute" >&2; exit 2 ;;
  esac
  local out vol muted=0 icon body
  out=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
  vol=$(pct_from_wpctl "$out")
  [[ $out == *MUTED* ]] && muted=1
  if (( muted || vol == 0 )); then
    icon=$icons/notification-audio-volume-muted.svg
  elif (( vol < 34 )); then
    icon=$icons/notification-audio-volume-low.svg
  elif (( vol < 67 )); then
    icon=$icons/notification-audio-volume-medium.svg
  else
    icon=$icons/notification-audio-volume-high.svg
  fi
  body="$vol%"
  (( muted )) && body="Muted"
  notify "$id_volume" "$icon" "Volume" "$body" "$vol"
}

brightness() {
  case ${1:-} in
    up)   brightnessctl -q set 10%+ ;;
    down) brightnessctl -q set 10%- ;;
    *)    echo "usage: ${0##*/} brightness up|down" >&2; exit 2 ;;
  esac
  local pct icon
  pct=$(brightnessctl -m | awk -F, '{ gsub(/%/, "", $4); print $4 }')
  if (( pct < 34 )); then
    icon=$icons/notification-display-brightness-low.svg
  elif (( pct < 67 )); then
    icon=$icons/notification-display-brightness-medium.svg
  else
    icon=$icons/notification-display-brightness-full.svg
  fi
  notify "$id_bright" "$icon" "Brightness" "${pct}%" "$pct"
}

mic() {
  wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
  local out vol muted=0 icon body
  out=$(wpctl get-volume @DEFAULT_AUDIO_SOURCE@)
  vol=$(pct_from_wpctl "$out")
  [[ $out == *MUTED* ]] && muted=1
  icon=$icons/notification-microphone-sensitivity-high.svg
  body="$vol%"
  if (( muted )); then
    icon=$icons/notification-microphone-sensitivity-muted.svg
    body="Muted"
  fi
  notify "$id_mic" "$icon" "Microphone" "$body" "$vol"
}

case ${1:-} in
  volume)     volume "${2:-}" ;;
  brightness) brightness "${2:-}" ;;
  mic)        mic ;;
  *)
    echo "usage: ${0##*/} volume up|down|mute | brightness up|down | mic" >&2
    exit 2
    ;;
esac
