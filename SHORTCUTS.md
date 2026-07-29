# Shortcuts

`SUPER` is the mod key. This file is generated from `hyprctl binds`, i.e. from the
descriptions in [`config/hypr/conf/binds.conf`](config/hypr/conf/binds.conf) — the
same source the in-session cheat sheet reads, so the two can't disagree.

**`SUPER + /` opens the live version of this list in rofi** — that one is read
straight from the running compositor, so treat it as the source of truth and this
file as the printable copy.

## Launch

| Keys | Action |
| --- | --- |
| `SUPER + RETURN` | Terminal |
| `SUPER + SHIFT + RETURN` | Terminal (kitty) |
| `SUPER + R` | App launcher |
| `SUPER + B` | Browser |
| `SUPER + E` | File manager |
| `SUPER + V` | Clipboard history |
| `SUPER + W` | Change wallpaper |
| `SUPER + slash` | Show these keybinds |

## Session

| Keys | Action |
| --- | --- |
| `SUPER + L` | Lock screen |
| `SUPER + X` | Power menu |
| `SUPER + SHIFT + M` | Exit Hyprland |
| `SUPER + SHIFT + B` | Restart waybar |
| `SUPER + CTRL + B` | Hide/show waybar |
| `SUPER + N` | Show last notification |
| `SUPER + SHIFT + N` | Dismiss all notifications |

## Windows

| Keys | Action |
| --- | --- |
| `SUPER + Q` | Close window |
| `SUPER + T` | Float/tile window |
| `SUPER + F` | Fullscreen |
| `SUPER + SHIFT + F` | Maximize (keep the bar) |
| `SUPER + C` | Center floating window |
| `SUPER + SHIFT + P` | Pin window to every workspace |
| `SUPER + P` | Pseudotile |
| `SUPER + J` | Toggle split direction |
| `SUPER + TAB` | Next window |
| `SUPER + SHIFT + TAB` | Previous window |
| `SUPER + left` | Focus left |
| `SUPER + right` | Focus right |
| `SUPER + up` | Focus up |
| `SUPER + down` | Focus down |
| `SUPER + SHIFT + left` | Move window left |
| `SUPER + SHIFT + right` | Move window right |
| `SUPER + SHIFT + up` | Move window up |
| `SUPER + SHIFT + down` | Move window down |
| `SUPER + CTRL + left` | Shrink window horizontally |
| `SUPER + CTRL + right` | Grow window horizontally |
| `SUPER + CTRL + up` | Shrink window vertically |
| `SUPER + CTRL + down` | Grow window vertically |
| `SUPER + Z` | Toggle scratchpad |
| `SUPER + SHIFT + Z` | Send window to scratchpad |

## Workspaces

| Keys | Action |
| --- | --- |
| `SUPER + 0` | Workspace 10 |
| `SUPER + 1` | Workspace 1 |
| `SUPER + 2` | Workspace 2 |
| `SUPER + 3` | Workspace 3 |
| `SUPER + 4` | Workspace 4 |
| `SUPER + 5` | Workspace 5 |
| `SUPER + 6` | Workspace 6 |
| `SUPER + 7` | Workspace 7 |
| `SUPER + 8` | Workspace 8 |
| `SUPER + 9` | Workspace 9 |
| `SUPER + A` | Workspace 11 |
| `SUPER + D` | Workspace 13 |
| `SUPER + G` | Workspace 14 |
| `SUPER + S` | Workspace 12 |
| `SUPER + grave` | Back to previous workspace |
| `SUPER + mouse_down` | Next workspace |
| `SUPER + mouse_up` | Previous workspace |
| `SUPER + SHIFT + 0` | Move window to workspace 10 |
| `SUPER + SHIFT + 1` | Move window to workspace 1 |
| `SUPER + SHIFT + 2` | Move window to workspace 2 |
| `SUPER + SHIFT + 3` | Move window to workspace 3 |
| `SUPER + SHIFT + 4` | Move window to workspace 4 |
| `SUPER + SHIFT + 5` | Move window to workspace 5 |
| `SUPER + SHIFT + 6` | Move window to workspace 6 |
| `SUPER + SHIFT + 7` | Move window to workspace 7 |
| `SUPER + SHIFT + 8` | Move window to workspace 8 |
| `SUPER + SHIFT + 9` | Move window to workspace 9 |
| `SUPER + SHIFT + A` | Move window to workspace 11 |
| `SUPER + SHIFT + S` | Move window to workspace 12 |
| `SUPER + SHIFT + D` | Move window to workspace 13 |
| `SUPER + SHIFT + G` | Move window to workspace 14 |

## Multi-monitor

| Keys | Action |
| --- | --- |
| `SUPER + ALT + left` | Focus the monitor to the left |
| `SUPER + ALT + right` | Focus the monitor to the right |
| `SUPER + ALT + SHIFT + left` | Move workspace to left monitor |
| `SUPER + ALT + SHIFT + right` | Move workspace to right monitor |

## Screenshots

| Keys | Action |
| --- | --- |
| `Print` | Screenshot region to clipboard |
| `SUPER + Print` | Screenshot region to file |
| `SUPER + SHIFT + Print` | Screenshot whole screen to clipboard |
| `SUPER + CTRL + Print` | Screenshot region and annotate |

## Media & hardware keys

| Keys | Action |
| --- | --- |
| `XF86AudioLowerVolume` | Volume down |
| `XF86AudioMicMute` | Mute microphone |
| `XF86AudioMute` | Mute output |
| `XF86AudioNext` | Next track |
| `XF86AudioPlay` | Play/pause |
| `XF86AudioPrev` | Previous track |
| `XF86AudioRaiseVolume` | Volume up |
| `XF86MonBrightnessDown` | Brightness down |
| `XF86MonBrightnessUp` | Brightness up |
| `XF86WLAN` | Toggle wifi |
| `switch:on:Lid Switch` | Lock on lid close |
| `SUPER + SPACE` | Play/pause |
| `SUPER + bracketleft` | Previous track |
| `SUPER + bracketright` | Next track |

## Mouse

| Action | Result |
| --- | --- |
| `SUPER` + drag left button | Move window |
| `SUPER` + drag right button | Resize window |
| `SUPER` + scroll | Next / previous workspace |
| Drag a window edge | Resize (grabbable from 15px outside, since borders are 0px) |

## Touchpad gestures

Configured in [`config/hypr/conf/gestures.conf`](config/hypr/conf/gestures.conf).

| Gesture | Action |
| --- | --- |
| 3 fingers horizontal | Switch workspace |
| 4 fingers up | Toggle scratchpad |
| 4 fingers down | Close the window under the cursor |

## Not bound on purpose

- `SUPER + M` used to exit Hyprland — one key away from `SUPER + N`, with no
  confirmation. It's `SUPER + SHIFT + M` now.
- Groups (tabbed windows) have no binds. `A/S/D/G` are workspace keys here, and
  the layout is dwindle; add `togglegroup` if you ever want them.

