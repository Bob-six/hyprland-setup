#!/usr/bin/env bash
# Waybar badge for dunst: history count + pause state.
set -euo pipefail

paused=$(dunstctl is-paused 2>/dev/null || echo true)
hist=$(dunstctl count history 2>/dev/null || echo 0)
wait=$(dunstctl count waiting 2>/dev/null || echo 0)
n=$((hist + wait))

if [[ $paused == true ]]; then
  printf '{"text":"󰂛","class":"paused","tooltip":"Notifications paused\\nLeft: show last\\nRight: unpause\\nMiddle: dismiss all"}\n'
elif (( n > 0 )); then
  printf '{"text":"󰂞  %s","class":"unread","tooltip":"%s in history\\nLeft: show last\\nRight: pause\\nMiddle: dismiss all"}\n' "$n" "$n"
else
  printf '{"text":"󰂚","class":"empty","tooltip":"No notifications\\nLeft: show last\\nRight: pause\\nMiddle: dismiss all"}\n'
fi
