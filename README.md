# hyprland

My Hyprland desktop, reproducible on a fresh Arch box. Validated against
**Hyprland 0.56.2** — `hyprctl configerrors` is clean and all 98 keybinds load.

Performance-first on purpose: animations, blur, shadows, rounding, gaps and
borders are all **off**, tearing and direct scanout are **on**. That's tuned for a
hybrid Intel/NVIDIA laptop — don't "fix" it.

## Install

```sh
git clone <this repo> ~/dvp/hyprland
cd ~/dvp/hyprland
./install.sh
```

Idempotent. It:

1. installs `packages.txt` — repo packages with `pacman`, anything else via `paru`/`yay`
2. **symlinks** `config/*` into `~/.config/*`, moving anything in the way to `*.bak.<timestamp>`
3. copies `wallpapers/` into `~/Pictures/wallpapers`, creates `~/Pictures/Screenshots`
4. creates `config/hypr/conf/host.lua` from the example if missing (gitignored)
5. enables NetworkManager, bluetooth, and the pipewire user units

Because the configs are symlinks, editing `~/.config/hypr/...` edits the repo. `git diff` is the sync.

Then: edit `host.lua` for the machine, log into Hyprland, and check `hyprctl configerrors`.

Lock-screen lockout is **not** part of that. It writes `/etc/pam.d` and `/etc/security`. Once, after install:

```sh
pkexec ~/.config/hypr/pam/install.sh
```

5 failed unlocks → 1 min, 10 → 5 min, 15 → 10 min. The tally lives in `/run/faillock-hypr`, separate from sudo.

## Per-machine config

Everything machine-specific lives in one gitignored file, `config/hypr/conf/host.lua`,
required last so it always wins: monitor modes, workspace→monitor pinning, GPU env vars.

`host.lua.example` defaults to every output at `preferred`/`auto` with no workspace
pinning, so a single-screen machine works untouched. My dual-screen layout (1–10 on
`eDP-1`, 11–14 on `HDMI-A-1`) is in there commented out, along with the NVIDIA-primary
env block. `hyprctl monitors` lists output names.

## Layout

```
config/
  hypr/
    hyprland.lua           requires everything below, host.lua last
    conf/                  environments, cursor, input, general, decoration,
                           animations, layouts, gestures, misc, windowrules,
                           binds, autostart, host.lua.example   (all .lua)
    hyprlock.conf  hypridle.conf  hyprpaper.conf  hyprsunset.conf
    scripts/               lock, screenshot, clipboard, wallpaper, keybinds,
                           osd, timetracker.py, taskwidget.py
    pam/                   staged hyprlock faillock; install with pkexec
  waybar/                  config, modules.json, style.css,
                           scripts/gpu.sh, workspace.py, dunst.sh
  rofi/                    config.rasi
  dunst/                   dunstrc
  wlogout/                 layout, style.css
  alacritty/  kitty/
wallpapers/                copied to ~/Pictures/wallpapers by install.sh
packages.txt
SHORTCUTS.md               printable copy of `hyprctl binds`
install.sh
```

## Shortcuts

See **[SHORTCUTS.md](SHORTCUTS.md)**, or hit `SUPER + /` in a session for the live list.

Every bind in `binds.lua` carries a `description`, and `hyprctl binds` reports it.
`scripts/keybinds.sh` renders that in rofi. `SHORTCUTS.md` is the printable copy;
`SUPER+/` reads the running compositor.

## Dead code that was removed

The old config was a half-removed [ML4W](https://github.com/mylinuxforwork/dotfiles)
install. These all pointed at things that did not exist:

| Removed | Why |
| --- | --- |
| `exec = ~/.config/ml4w-hyprland-settings/hyprctl.sh` in autostart | that directory doesn't exist |
| waybar network `on-click` → `ml4w/settings/networkmanager.sh`, `on-click-right` → `ml4w/scripts/nm-applet.sh` | neither script exists → now `nm-connection-editor` / `nmtui` |
| `ml4w/scripts/keybindings.sh` | read a `keybindings.conf` that doesn't exist → replaced by `hypr/scripts/keybinds.sh` |
| `group/quicklinks` + `waybar-quicklinks.json` | launched `flatpak run com.ml4w.hyprlandsettings`, not installed |
| `mpd` module in `modules-right` | never defined in `modules.json`, no mpd installed |
| `ml4w/apps/ML4W_Hyprland_Settings-x86_64.AppImage` | an AppImage GUI editing configs this repo now owns |
| `hypr/conf/monitor.conf` | duplicated the monitor lines that `binds.lua` also set |
| `split-monitor-workspaces` plugin block in `binds.lua` | plugin not installed, every one of its binds commented out |
| `gestures { workspace_swipe }` | **option no longer exists in 0.55** — `hyprctl getoption gestures:workspace_swipe` → "no such option". Rewritten with the current `gesture =` syntax |
| `bind = , XF86Refresh, exec, xdotool key F5` | xdotool is X11-only, does nothing under Wayland |
| `reload-waybar.sh` / `reload-hyprpaper.sh` | `killall -9` + `sleep 1` + respawn → `killall -SIGUSR1 waybar` and hyprpaper's IPC |
| `master { }`, empty `gestures { }`, `.aider*` files, `*.bak` configs, `alacritty.yml` | empty or stale |

## Bugs fixed

- **`bubd = $mainMod, G, exec, playerctl play-pause`** — typo for `bind`, so it never
  bound anything. `G` was already workspace 14 anyway.
- **`SUPER + Print`** ran `$(date ...)` twice in one command line, so `grim` wrote one
  filename and `wl-copy` read a different, non-existent one. Now `screenshot.sh`.
- **Workspaces pinned to `eDP-1`/`HDMI-A-1`** in the shared config — on any other
  machine those workspaces attach to a monitor that isn't there. Moved to `host.lua`.
- **`gpu.sh`** printed `GPU n/a` forever without nvidia-smi; now returns empty text so
  waybar hides the module.
- **`hyprland/workspaces` and `idle_inhibitor`** were configured in `modules.json` but
  never listed in the bar, so neither ever appeared. Both are on it now.
- **`hyprsunset.conf`** existed but nothing ever started `hyprsunset`.
- **`OZONE_PLATFORM=wayland`** — not a variable Electron reads; it's
  `ELECTRON_OZONE_PLATFORM_HINT`.
- **`nm-applet`** was started without `--indicator`, so its tray icon never showed
  under waybar's SNI tray.
- Fonts and themes the configs demand (`JetBrainsMono Nerd`, `Inter`, `qt6ct`,
  `Papirus-Dark`) were **not installed** — they're in `packages.txt` now.

## Added

Hyprland features the old config didn't use, all verified against this 0.55.4 build:

- **Bind descriptions** (`bindd`) + the self-updating cheat sheet.
- **Scratchpad** (`SUPER+Z`) — a special workspace toggled over the current one.
- **Window move / resize binds** (`SUPER+SHIFT+arrows`, `SUPER+CTRL+arrows`, repeating
  while held via the `e` flag). Previously there was no way to move a window by keyboard.
- **`bindl` on media, mute, wifi and lid keys** so they work while the screen is locked;
  lid close now locks the session before suspend.
- **Touchpad gestures** in the current syntax: 3-finger swipe to change workspace,
  4-finger up for the scratchpad, 4-finger down to close.
- **`general:snap`** — floating windows snap to edges; **`extend_border_grab_area = 15`**
  so you can still grab an edge with 0px borders.
- **`binds:workspace_back_and_forth`** and `SUPER+grave` for the previous workspace.
- **`ecosystem:no_update_news` / `no_donation_nag`** — no banners on login.
- **`cursor:hide_on_key_press`**, **`input:touchpad:disable_while_typing`**,
  **`clickfinger_behavior`**, **`special_fallthrough`**, **`dwindle:smart_resizing`**,
  **`misc:close_special_on_empty`**, **`xwayland:force_zero_scaling`**.
- **Window rules**: dialogs (pavucontrol, nm-connection-editor, file pickers) float
  centered at 60%; Picture-in-Picture floats pinned; `idle_inhibit fullscreen` on
  video players so the screen never blanks mid-film; `suppress_event maximize`.
- **hypridle** dims the backlight at 4 min as a warning before the 5 min lock.
- **hyprlock** shows the active keyboard layout, so a rejected password explains itself.
- **Clipboard history** (`cliphist` + `SUPER+V`) and a **wallpaper picker**
  (`SUPER+W`) that applies over hyprpaper's IPC and persists the choice.
- **hyprpolkitagent** so GUI apps can actually ask for a password.
- **waybar**: bluetooth, keyboard layout, idle inhibitor, a scrollable calendar,
  and a memory tooltip. The per-output workspace strip from this pass was later
  replaced by a single active-workspace label — see below.

## Since the 0.55 cleanup

Running session is **0.56.2**. Same check: `hyprctl configerrors` is empty.

### Desktop widgets

`timetracker.py` and `taskwidget.py` start with the session. Both are
gtk-layer-shell windows on the **bottom** layer, so they sit behind tiled and
floating windows on every workspace. Drag to move; the position is remembered.
`SUPER+SHIFT+T` / `SUPER+SHIFT+K` bring one back after you quit it.

| Widget | Data |
| --- | --- |
| Time tracker (top-right) | `~/.local/share/timetracker/entries.csv` |
| Tasks (top-left) | `~/.local/share/taskwidget/tasks.json` |

Time tracker is Clockify-style: type a task, Start, Stop. A running session
survives a widget restart. logind `PrepareForShutdown` stops it and writes the
row; if the process is killed first, the next launch closes a session that
started before this boot, at its last heartbeat.

Tasks: Enter or Add to insert, check to complete, ✕ to delete. A leading `!`
is high priority. Completed tasks sit in the header popover.

`packages.txt` pulls `python-gobject`, `python-cairo`, `gtk3`, and
`gtk-layer-shell` for them. Blur behind the cards is the `gtk-layer-shell`
layer rule.

### OSD, notifications, bar

Volume, brightness, and mic keys go through `scripts/osd.sh`, and so do waybar's
volume scroll and right-click. Dunst draws the progress bar (`dunstify`).
Toasts from app `osd` stay visible in fullscreen; other toasts are pushed back
until you leave it. Critical ones still show.

Dunst uses the same glass palette as rofi, follows the last-interacted output
(don't pin `monitor = 0` on a dual-screen box), and prefixes the body with an
LRM so Persian/Arabic lines don't stick to the right edge. Telegram drops the
app name, since the icon already says it. Blur is a layer rule on the
`notifications` namespace (`ignore_alpha = 0`, or the translucent fill is
treated as opaque).

Waybar does not draw every workspace. `hyprland/workspaces` still painted
`host.lua`'s persistent pins 1–14. `scripts/workspace.py` listens on the event
socket and prints only the active workspace on that output. `custom/dunst` is
the history count: left pops the last notification, right pauses, middle
dismisses all. `SUPER+ALT+N` toggles pause too.

### Other fixes

- **Screenshots.** Esc on slurp used to run `grim` with an empty geometry and
  wipe the clipboard. The geometry is assigned first, so `set -e` aborts.
  The toast shows the image.
- **Night light.** 21:00 was `20000K`. That is the bluest step, and the `K`
  suffix is not a valid token. The profile is `4000` (warm) now.
- **Launcher PATH.** `SUPER+R` inherits the compositor environment. systemd's
  default is `/usr/local/bin:/usr/bin`, so `~/.local/bin` apps failed to launch.
  `environments.lua` prepends `~/.local/bin`, and autostart exports `PATH` on
  the dbus activation environment.
- **Telegram webview.** A native-Wayland GTK4 helper detaches, tiles, and grows
  until it crashes. The window rule floats it, centered, at half the monitor.
  Fullscreen Telegram also inhibits idle. The usual launch path is the XWayland
  embed in `~/.local/bin/telegram`; the rule is the backstop.
- **Wallpaper picker** notifies with the new image.
- **`SUPER+SHIFT+Q`** force-kills the focused window.
- **`packages.txt`** now includes `google-chrome-stable` (`SUPER+B`) and `btop`
  (waybar system modules open it on click).
- **Lock wallpaper** is `~/Pictures/wallpapers/wallpaper8-electric-wilderness.jpg`.
  That file is not in this repo. Point `hyprlock.conf` at one under `wallpapers/`
  if the path is missing.

## Notes

- **Not** managed here: display manager. Use `sddm`/`greetd`, or start from a TTY.
- Keyboard is `us,ir`, `ALT+SHIFT` toggles. `lock.sh` forces layout 0 before locking so
  the password types in English.
- `keyboard-state` (numlock/capslock) was dropped from the bar in favour of the layout
  indicator, which matters more with two layouts. Add it back in `modules-right` if you miss it.
- The compositor config is Lua (`hyprland.lua`): hyprlang is deprecated since
  Hyprland 0.55 and `hyprland.conf` support is being removed. `hyprlock`, `hypridle`,
  `hyprpaper` and `hyprsunset` are separate programs and still read their own
  `.conf` files.
