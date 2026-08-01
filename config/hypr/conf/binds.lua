-- Docs: https://wiki.hypr.land/Configuring/Basics/Binds/
--
-- Every bind carries a `description`. `hyprctl binds` reports those
-- descriptions, and that is what the SUPER+/ cheat sheet renders — so a bind
-- documented here can never drift out of sync with the docs.
--
-- Flags used below:
--   repeating  repeats while held      (volume, brightness, resize)
--   locked     fires even when locked  (media and hardware keys)
--   mouse      mouse bind

local mainMod = "SUPER"
local term = "alacritty"
local browser = "google-chrome-stable"
local files = "thunar"
local scripts = os.getenv("HOME") .. "/.config/hypr/scripts"

-- Shorthand: bind(keys, description, dispatcher, extra_flags?)
local function bind(keys, description, dispatcher, flags)
    flags = flags or {}
    flags.description = description
    hl.bind(keys, dispatcher, flags)
end

local function exec(cmd)
    return hl.dsp.exec_cmd(cmd)
end

-- ── Launch ─────────────────────────────────────────────────────────
bind(mainMod .. " + RETURN", "Terminal", exec(term))
bind(mainMod .. " + SHIFT + RETURN", "Terminal (kitty)", exec("kitty"))
bind(mainMod .. " + R", "App launcher", exec("rofi -show drun -replace"))
bind(mainMod .. " + B", "Browser", exec(browser))
bind(mainMod .. " + E", "File manager", exec(files))
bind(mainMod .. " + V", "Clipboard history", exec(scripts .. "/clipboard.sh"))
bind(mainMod .. " + W", "Change wallpaper", exec(scripts .. "/wallpaper.sh"))
bind(mainMod .. " + slash", "Show these keybinds", exec(scripts .. "/keybinds.sh"))

-- ── Session ────────────────────────────────────────────────────────
bind(mainMod .. " + L", "Lock screen", exec(scripts .. "/lock.sh"))
bind(mainMod .. " + X", "Power menu", exec("wlogout -b 4"))
bind(mainMod .. " + SHIFT + M", "Exit Hyprland", hl.dsp.exit())
bind(mainMod .. " + SHIFT + B", "Restart waybar", exec("killall waybar; waybar & disown"))
bind(mainMod .. " + CTRL + B", "Hide/show waybar", exec("killall -SIGUSR1 waybar"))
bind(mainMod .. " + N", "Show last notification", exec("dunstctl history-pop"))
bind(mainMod .. " + SHIFT + N", "Dismiss all notifications", exec("dunstctl close-all"))

-- ── Window ─────────────────────────────────────────────────────────
bind(mainMod .. " + Q", "Close window", hl.dsp.window.close())
bind(mainMod .. " + T", "Float/tile window", hl.dsp.window.float({ action = "toggle" }))
bind(mainMod .. " + F", "Fullscreen", hl.dsp.window.fullscreen({ mode = "fullscreen", action = "toggle" }))
bind(mainMod .. " + SHIFT + F", "Maximize (keep the bar)", hl.dsp.window.fullscreen({ mode = "maximized", action = "toggle" }))
bind(mainMod .. " + C", "Center floating window", hl.dsp.window.center())
bind(mainMod .. " + SHIFT + P", "Pin window to every workspace", hl.dsp.window.pin({ action = "toggle" }))
bind(mainMod .. " + P", "Pseudotile", hl.dsp.window.pseudo())
bind(mainMod .. " + J", "Toggle split direction", hl.dsp.layout("togglesplit"))
bind(mainMod .. " + TAB", "Next window", hl.dsp.window.cycle_next())
bind(mainMod .. " + SHIFT + TAB", "Previous window", hl.dsp.window.cycle_next({ next = false }))

local directions = { left = "left", right = "right", up = "up", down = "down" }
for key, dir in pairs(directions) do
    bind(mainMod .. " + " .. key, "Focus " .. dir, hl.dsp.focus({ direction = dir }))
    bind(mainMod .. " + SHIFT + " .. key, "Move window " .. dir, hl.dsp.window.move({ direction = dir }))
end

local resizes = {
    { "left",  "Shrink window horizontally", -40, 0 },
    { "right", "Grow window horizontally",    40, 0 },
    { "up",    "Shrink window vertically",     0, -40 },
    { "down",  "Grow window vertically",       0, 40 },
}
for _, r in ipairs(resizes) do
    bind(mainMod .. " + CTRL + " .. r[1], r[2],
        hl.dsp.window.resize({ x = r[3], y = r[4], relative = true }), { repeating = true })
end

-- Scratchpad — a hidden workspace toggled over whatever you are on
bind(mainMod .. " + Z", "Toggle scratchpad", hl.dsp.workspace.toggle_special("magic"))
bind(mainMod .. " + SHIFT + Z", "Send window to scratchpad",
    hl.dsp.window.move({ workspace = "special:magic", follow = false }))

-- ── Workspaces ─────────────────────────────────────────────────────
-- 1-10 on the primary screen, 11-14 on the second — pinning lives in conf/host.lua
local workspaceKeys = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "A", "S", "D", "G" }
for i, key in ipairs(workspaceKeys) do
    bind(mainMod .. " + " .. key, "Workspace " .. i, hl.dsp.focus({ workspace = i }))
    bind(mainMod .. " + SHIFT + " .. key, "Move window to workspace " .. i, hl.dsp.window.move({ workspace = i }))
end

bind(mainMod .. " + grave", "Back to previous workspace", hl.dsp.focus({ workspace = "previous" }))

-- ── Multi-monitor ──────────────────────────────────────────────────
bind(mainMod .. " + ALT + left", "Focus the monitor to the left", hl.dsp.focus({ monitor = "l" }))
bind(mainMod .. " + ALT + right", "Focus the monitor to the right", hl.dsp.focus({ monitor = "r" }))
bind(mainMod .. " + ALT + SHIFT + left", "Move workspace to left monitor", hl.dsp.workspace.move({ monitor = "l" }))
bind(mainMod .. " + ALT + SHIFT + right", "Move workspace to right monitor", hl.dsp.workspace.move({ monitor = "r" }))

-- ── Screenshots ────────────────────────────────────────────────────
bind("Print", "Screenshot region to clipboard", exec(scripts .. "/screenshot.sh region"))
bind(mainMod .. " + Print", "Screenshot region to file", exec(scripts .. "/screenshot.sh save"))
bind(mainMod .. " + SHIFT + Print", "Screenshot whole screen to clipboard", exec(scripts .. "/screenshot.sh screen"))
bind(mainMod .. " + CTRL + Print", "Screenshot region and annotate", exec(scripts .. "/screenshot.sh edit"))

-- ── Media & hardware keys ──────────────────────────────────────────
local held = { locked = true, repeating = true }
bind("XF86AudioRaiseVolume", "Volume up", exec("wpctl set-volume -l 1.4 @DEFAULT_AUDIO_SINK@ 5%+"), held)
bind("XF86AudioLowerVolume", "Volume down", exec("wpctl set-volume -l 1.4 @DEFAULT_AUDIO_SINK@ 5%-"), held)
bind("XF86MonBrightnessUp", "Brightness up", exec("brightnessctl set 10%+"), held)
bind("XF86MonBrightnessDown", "Brightness down", exec("brightnessctl set 10%-"), held)

local locked = { locked = true }
bind("XF86AudioMute", "Mute output", exec("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"), locked)
bind("XF86AudioMicMute", "Mute microphone", exec("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"), locked)
bind("XF86WLAN", "Toggle wifi", exec("nmcli radio wifi toggle"), locked)
bind("XF86AudioPlay", "Play/pause", exec("playerctl play-pause"), locked)
bind("XF86AudioNext", "Next track", exec("playerctl next"), locked)
bind("XF86AudioPrev", "Previous track", exec("playerctl previous"), locked)

bind(mainMod .. " + SPACE", "Play/pause", exec("playerctl play-pause"))
bind(mainMod .. " + bracketright", "Next track", exec("playerctl next"))
bind(mainMod .. " + bracketleft", "Previous track", exec("playerctl previous"))

-- Lid close locks the session before suspend, so nothing is on screen on wake
bind("switch:on:Lid Switch", "Lock on lid close", exec("loginctl lock-session"), { locked = true })

-- ── Mouse ──────────────────────────────────────────────────────────
hl.bind(mainMod .. " + mouse:272", hl.dsp.window.drag(), { mouse = true })
hl.bind(mainMod .. " + mouse:273", hl.dsp.window.resize(), { mouse = true })
bind(mainMod .. " + mouse_down", "Next workspace", hl.dsp.focus({ workspace = "e+1" }))
bind(mainMod .. " + mouse_up", "Previous workspace", hl.dsp.focus({ workspace = "e-1" }))
