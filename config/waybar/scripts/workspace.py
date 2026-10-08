#!/usr/bin/env python3
"""Print this bar's active Hyprland workspace, one line per change.

Waybar's hyprland/workspaces active-only flag still draws workspaces that
Hyprland marks persistent. This replaces that strip with a single name.
"""

import json
import os
import socket
import subprocess

EVENTS = (
    "workspace>>",
    "workspacev2>>",
    "focusedmon>>",
    "focusedmonv2>>",
    "moveworkspace>>",
    "moveworkspacev2>>",
    "createworkspace>>",
    "destroyworkspace>>",
    "configreloaded>>",
    "monitoradded>>",
    "monitorremoved>>",
)


def active_name():
    raw = subprocess.check_output(["hyprctl", "monitors", "-j"], text=True)
    monitors = json.loads(raw)
    want = os.environ.get("WAYBAR_OUTPUT_NAME", "")
    chosen = None
    for mon in monitors:
        if want and mon.get("name") == want:
            chosen = mon
            break
    if chosen is None:
        for mon in monitors:
            if mon.get("focused"):
                chosen = mon
                break
    if chosen is None and monitors:
        chosen = monitors[0]
    if not chosen:
        return ""
    ws = chosen.get("activeWorkspace") or {}
    return str(ws.get("name") or "")


def emit(last):
    try:
        name = active_name()
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
        return last
    if name and name != last:
        print(name, flush=True)
        return name
    return last


def main():
    last = emit("")
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
    runtime = os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    path = os.path.join(runtime, "hypr", sig, ".socket2.sock")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(path)
    buf = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            text = line.decode("utf-8", "replace")
            if text.startswith(EVENTS):
                last = emit(last)


if __name__ == "__main__":
    main()
