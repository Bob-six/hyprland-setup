-- Docs: https://wiki.hypr.land/Configuring/Layouts/Dwindle-Layout/
hl.config({
    dwindle = {
        preserve_split = true, -- keep the split direction when windows close
        smart_split = false,   -- true = split follows where in the window you drop
        smart_resizing = true, -- resize picks the neighbour you'd expect
    },
})

-- The master layout is unused (general.layout = dwindle), so it is not
-- configured here. Switch with `hyprctl keyword general:layout master` to try it.
