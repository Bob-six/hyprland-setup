-- Docs: https://wiki.hypr.land/Configuring/Basics/Window-Rules/
-- Lua syntax: hl.window_rule({ name = ..., match = { <props> }, <effects> })

-- ── Tearing: lower input latency in fullscreen games ───────────────
hl.window_rule({ name = "tearing-steam", match = { class = "^(steam_app_.*)$" }, immediate = true })
hl.window_rule({ name = "tearing-games", match = { class = "^(cs2|gamescope)$" }, immediate = true })

-- ── Small dialogs belong in a floating, centered window ────────────
hl.window_rule({
    name  = "float-settings-dialogs",
    match = { class = "^(pavucontrol|blueman-manager|nm-connection-editor)$" },
    float = true,
    center = true,
    size  = { "monitor_w*0.6", "monitor_h*0.6" },
})
hl.window_rule({ name = "float-pavucontrol", match = { class = "^(org.pulseaudio.pavucontrol)$" }, float = true })
hl.window_rule({ name = "float-theme-tools", match = { class = "^(qt6ct|nwg-look)$" }, float = true })
hl.window_rule({
    name  = "float-file-pickers",
    match = { title = "^(Open File|Open Folder|Save As|Save File|Choose Files)$" },
    float = true,
})

-- Picture-in-picture: float it, keep it on top of everything, follow me around
hl.window_rule({
    name  = "pip",
    match = { title = "^(Picture-in-Picture)$" },
    float = true,
    pin   = true,
    size  = { "monitor_w*0.25", "monitor_h*0.25" },
})

-- ── Don't let the screen blank mid-video ───────────────────────────
hl.window_rule({
    name  = "idle-inhibit-players",
    match = { class = "^(mpv|vlc|google-chrome|chromium|brave-browser|firefox)$" },
    idle_inhibit = "fullscreen",
})

-- ── Apps that try to maximize themselves on launch ─────────────────
hl.window_rule({ name = "suppress-maximize", match = { class = "^(.*)$" }, suppress_event = "maximize" })

-- ── Layer rules ────────────────────────────────────────────────────
-- Blur behind rofi: its background is translucent (see rofi/config.rasi),
-- so this is one layer's worth of GPU cost, only while the launcher is open.
hl.layer_rule({ name = "rofi-blur", match = { namespace = "^(rofi)$" }, blur = true, ignore_alpha = 0.2 })
