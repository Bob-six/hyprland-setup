-- Docs: https://wiki.hypr.land/Configuring/Basics/Variables/
hl.config({
    general = {
        gaps_in = 0,
        gaps_out = 0,
        border_size = 0,
        col = {
            active_border = { colors = { "rgba(33ccffee)", "rgba(00ff99ee)" }, angle = 45 },
            inactive_border = "rgba(595959aa)",
        },
        layout = "dwindle",
        resize_on_border = true,
        allow_tearing = true, -- fullscreen games may tear -> lower input latency (see windowrules.lua)

        -- border_size is 0, so let the pointer grab a window edge from just outside it
        extend_border_grab_area = 15,

        -- Drag a floating window near an edge and it snaps there
        snap = {
            enabled = true,
            window_gap = 10,
            monitor_gap = 10,
        },
    },
})
