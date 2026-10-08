hl.config({
    cursor = {
        -- Software cursors: required on NVIDIA (hardware planes glitch), harmless
        -- elsewhere. Flip it in conf/host.lua on an Intel/AMD-only machine.
        no_hardware_cursors = true,

        -- Hide the pointer while typing, bring it back on move. Small nicety,
        -- no runtime cost.
        hide_on_key_press = true,
        inactive_timeout = 10,

        -- The cursor *theme* is set by XCURSOR_THEME in conf/environments.lua,
        -- not here. cursor:default_monitor takes an output name (e.g. "eDP-1")
        -- and only decides where the pointer lands at startup.
    },
})
