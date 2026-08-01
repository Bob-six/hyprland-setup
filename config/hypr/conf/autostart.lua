-- Docs: https://wiki.hypr.land/Configuring/Basics/Autostart/

hl.on("hyprland.start", function()
    hl.exec_cmd("waybar")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("dunst")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("hyprsunset") -- night-light schedule, see hyprsunset.conf
    hl.exec_cmd("systemctl --user start hyprpolkitagent") -- GUI password prompts
    hl.exec_cmd("nm-applet --indicator")

    -- Clipboard history, read back with SUPER+V
    hl.exec_cmd("wl-paste --type text --watch cliphist store")
    hl.exec_cmd("wl-paste --type image --watch cliphist store")

    -- Make xdg-desktop-portal see the session env (screen sharing, file pickers)
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
end)
