-- Session env. GPU-specific vars live in conf/host.lua.

hl.env("XDG_CURRENT_DESKTOP", "Hyprland")
hl.env("XDG_SESSION_TYPE", "wayland")
hl.env("XDG_SESSION_DESKTOP", "Hyprland")

-- Qt
hl.env("QT_QPA_PLATFORM", "wayland;xcb")
hl.env("QT_QPA_PLATFORMTHEME", "qt6ct")
hl.env("QT_WAYLAND_DISABLE_WINDOWDECORATION", "1")
hl.env("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

-- GTK
hl.env("GDK_SCALE", "1")

-- Firefox
hl.env("MOZ_ENABLE_WAYLAND", "1")

-- Chromium/Electron apps: this is the var they actually read. Plain
-- OZONE_PLATFORM does nothing on its own.
hl.env("ELECTRON_OZONE_PLATFORM_HINT", "auto")

hl.env("XCURSOR_SIZE", "24")
hl.env("XCURSOR_THEME", "Adwaita")

hl.env("HYPRCURSOR_THEME", "Adwaita") -- optional, if you have a hyprcursor version
hl.env("HYPRCURSOR_SIZE", "24")

-- Don't let appimaged hijack AppImage launches
hl.env("APPIMAGELAUNCHER_DISABLE", "1")
