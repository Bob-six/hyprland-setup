-- Docs: https://wiki.hypr.land/Configuring/Gestures/
-- The old `gestures { workspace_swipe = ... }` block was removed in 0.55.

-- Three fingers sideways on the touchpad = switch workspace
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })

-- Four fingers up = scratchpad, four down = close the window under the cursor
hl.gesture({ fingers = 4, direction = "up", action = "special", workspace_name = "magic" })
hl.gesture({ fingers = 4, direction = "down", action = "close" })
