--  _   _                  _                 _
-- | | | |_   _ _ __  _ __| | __ _ _ __   __| |
-- | |_| | | | | '_ \| '__| |/ _` | '_ \ / _` |
-- |  _  | |_| | |_) | |  | | (_| | | | | (_| |
-- |_| |_|\__, | .__/|_|  |_|\__,_|_| |_|\__,_|
--        |___/|_|
--
-- Docs: https://wiki.hypr.land
-- Performance-first: animations/blur/shadows/rounding are off on purpose.
--
-- Lua, not hyprlang: hyprlang is deprecated since Hyprland 0.55 and
-- hyprland.conf support is going away. Paths are relative to this file.

require("conf/environments")
require("conf/cursor")
require("conf/input")
require("conf/general")
require("conf/decoration")
require("conf/animations")
require("conf/layouts")
require("conf/gestures")
require("conf/misc")
require("conf/windowrules")
require("conf/binds")
require("conf/autostart")

-- Per-machine overrides: monitors, workspace pinning, GPU env.
-- Gitignored, generated from host.lua.example by install.sh. Required last so it wins.
require("conf/host")
