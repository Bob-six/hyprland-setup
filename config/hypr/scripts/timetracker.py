#!/usr/bin/env python3
"""
Time Tracker — Clockify-style desktop widget for Hyprland.

A small widget drawn in the Wayland *bottom* layer (via gtk-layer-shell),
so it sits behind every window — tiled and floating — like a Conky-style
desktop widget. It shows on all workspaces and defaults to the top-right,
just below the waybar; drag it anywhere with the mouse and the position is
remembered. (The background layer would also work but gets covered by the
wallpaper, which lives in the same layer.)

Type a task name, hit Start, hit Stop when done. Every session is appended to:

    ~/.local/share/timetracker/entries.csv   (start, end, duration_sec, task)

A running session survives widget restarts (state is kept in running.json),
so closing or restarting the widget never loses the running timer.

System shutdown stops the running task and logs the session (logind
PrepareForShutdown). If the process is killed first, the next launch closes
a session that started before this boot, at its last heartbeat.

SUPER+SHIFT+T brings the widget back up after it was quit.
"""

import csv
import fcntl
import json
import math
import os
import subprocess
import sys
import time
from datetime import date, datetime

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell, Pango
import cairo

APP_ID = "dev.timetracker"
DATA_DIR = os.path.expanduser("~/.local/share/timetracker")
CSV_PATH = os.path.join(DATA_DIR, "entries.csv")
STATE_PATH = os.path.join(DATA_DIR, "running.json")
POS_PATH = os.path.join(DATA_DIR, "position.json")
FIELDS = ["start", "end", "duration_sec", "task"]

# Default spot on first launch: the waybar sits at the top of the screen
# (and reserves that space), so a small top margin drops us just below it,
# and RIGHT_MARGIN keeps us 16px off the right edge. After that, the
# drag-to-move position is remembered.
TOP_MARGIN = 8
RIGHT_MARGIN = 16
CARD_WIDTH = 300

# Glass Tokyo-Night / Catppuccin, matching rofi + dunst + taskwidget.
CSS = b"""
@define-color bg rgba(20, 22, 30, 0.01);
@define-color fg #e0e6f0;
@define-color muted #a9b1d6;
@define-color subtle #565f89;
@define-color overlay rgba(255, 255, 255, 0.06);
@define-color accent #7aa2f7;
@define-color green #a6e3a1;
@define-color teal #94e2d5;
@define-color red #f7768e;
@define-color peach #fab387;
@define-color surface #1a1b26;

* {
  font-family: "Inter", "Iosevka Nerd Font", "JetBrains Mono", sans-serif;
  font-size: 13px;
  color: @fg;
  outline: none;
  -gtk-outline-radius: 0;
}

window { background: transparent; }

button {
  background-image: none;
  background: transparent;
  border: none;
  box-shadow: none;
  text-shadow: none;
  min-height: 0;
  min-width: 0;
  padding: 0;
  color: @fg;
}
button:hover, button:active, button:checked, button:disabled {
  background-image: none;
  box-shadow: none;
  text-shadow: none;
}

entry {
  background-image: none;
  box-shadow: none;
  border: none;
  caret-color: @accent;
}

eventbox.card, .card { background-color: transparent; }

.accent-dot { color: @subtle; font-size: 10px; }
.accent-dot.live {
  color: @green;
  animation: pulse 1.1s ease-in-out infinite alternate;
}
@keyframes pulse {
  from { opacity: 1; }
  to { opacity: 0.35; }
}

.brand {
  color: @muted;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1.8px;
}

separator.hairline {
  background: rgba(255, 255, 255, 0.07);
  min-height: 1px;
}

button.pill {
  background-image: none;
  background-color: rgba(122, 162, 247, 0.18);
  color: @accent;
  font-size: 11px;
  font-weight: 700;
  border-radius: 999px;
  padding: 2px 9px;
  min-height: 20px;
}
button.pill label { color: @accent; font-weight: 700; }
button.pill:hover, button.pill:checked {
  background-image: none;
  background-color: rgba(122, 162, 247, 0.30);
}
button.pill:hover label, button.pill:checked label { color: @fg; }

button.quit {
  color: @subtle;
  font-size: 11px;
  font-weight: 700;
  min-width: 22px;
  min-height: 22px;
  border-radius: 999px;
}
button.quit:hover {
  background: rgba(247, 118, 142, 0.18);
  color: @red;
}

.entry {
  background: @overlay;
  color: @fg;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 11px;
  padding: 9px 12px;
  font-size: 13px;
  min-height: 20px;
}
.entry:focus { border-color: rgba(122, 162, 247, 0.55); }
.entry:disabled {
  background: rgba(166, 227, 161, 0.08);
  color: @fg;
  border-color: rgba(166, 227, 161, 0.28);
}

.elapsed {
  color: @fg;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 0.8px;
  font-feature-settings: "tnum";
  font-family: "Iosevka Nerd Font", "JetBrains Mono", monospace;
}
.elapsed.live { color: @green; }

button.play {
  min-width: 40px;
  min-height: 40px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
}
button.start { background: @green; color: @surface; }
button.start:hover { background: @teal; }
button.stop { background: @red; color: @surface; }
button.stop:hover { background: @peach; }

.history-task { color: @fg; font-size: 12px; }
.history-task.live { color: @green; }
.history-time { color: @muted; font-size: 11px; font-feature-settings: "tnum"; }
.empty { color: @subtle; font-size: 12px; }

popover {
  background: @surface;
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 12px;
}
button.open-log {
  background: transparent;
  color: @accent;
  font-size: 11px;
  border-radius: 8px;
  padding: 4px 8px;
}
button.open-log:hover { background: rgba(255, 255, 255, 0.08); color: @fg; }
"""

_LOCK = None


def _fmt_clock(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}"


def _fmt_dur(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def _read_entries():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _today_total(entries):
    today = date.today().isoformat()
    total = 0.0
    for e in entries:
        if e.get("start", "").startswith(today):
            try:
                total += float(e["duration_sec"])
            except (KeyError, ValueError):
                pass
    return total


def _today_count(entries):
    today = date.today().isoformat()
    return sum(1 for e in entries if e.get("start", "").startswith(today))


def _recent_tasks(entries):
    seen, out = set(), []
    for e in reversed(entries):
        t = (e.get("task") or "").strip()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _parse_iso(raw):
    if not isinstance(raw, str):
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def _boot_time():
    try:
        with open("/proc/stat", encoding="utf-8") as f:
            for line in f:
                if line.startswith("btime "):
                    return datetime.fromtimestamp(int(line.split()[1]))
    except (OSError, ValueError):
        return None
    return None


def _previous_boot_end():
    """Last journal line of the previous boot. Stands in for shutdown time
    when a running session has no heartbeat (written by an older widget)."""
    try:
        out = subprocess.check_output(
            [
                "journalctl", "-b", "-1", "-o", "short-unix",
                "-n", "1", "--no-pager", "-q",
            ],
            text=True,
            timeout=3,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    lines = out.strip().splitlines()
    if not lines:
        return None
    try:
        return datetime.fromtimestamp(float(lines[-1].split()[0]))
    except (ValueError, IndexError):
        return None


def _session_end_after_reboot(state, boot):
    """End time if this session started before the current boot, else None.

    Widget restarts in the same boot keep the timer. A reboot means the
    machine was off, so the open session is over.
    """
    if boot is None:
        return None
    started = _parse_iso(state.get("start"))
    if started is None or started >= boot:
        return None
    beat = _parse_iso(state.get("heartbeat"))
    if beat is not None and started <= beat < boot:
        return beat
    prev = _previous_boot_end()
    if prev is not None and started <= prev < boot:
        return prev
    return started


def _write_entry(start_iso, end_iso, duration_sec, task):
    os.makedirs(DATA_DIR, exist_ok=True)
    fresh = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if fresh:
            writer.writeheader()
        writer.writerow({
            "start": start_iso,
            "end": end_iso,
            "duration_sec": f"{duration_sec:.0f}",
            "task": task,
        })
        f.flush()
        os.fsync(f.fileno())


def _entry_logged(start_iso):
    try:
        return any(e.get("start") == start_iso for e in _read_entries())
    except OSError:
        return False


def _finish_if_rebooted(state):
    """Log and drop a session that was still open when the machine booted."""
    if not state or not state.get("task") or not state.get("start"):
        return None
    end = _session_end_after_reboot(state, _boot_time())
    if end is None:
        return state
    started = _parse_iso(state["start"])
    if started is None:
        return None
    if end < started:
        end = started
    if not _entry_logged(state["start"]):
        _write_entry(
            state["start"],
            end.isoformat(timespec="seconds"),
            (end - started).total_seconds(),
            state["task"],
        )
    try:
        os.remove(STATE_PATH)
    except OSError:
        pass
    return None


def _add_class(widget, name):
    widget.get_style_context().add_class(name)


def _rounded_rect(cr, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(w - r, r, r, -math.pi / 2, 0)
    cr.arc(w - r, h - r, r, 0, math.pi / 2)
    cr.arc(r, h - r, r, math.pi / 2, math.pi)
    cr.arc(r, r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def _draw_glass(cr, w, h, r, border):
    # Fill matches rofi glass (rgba(20,22,30,0.78)); compositor blurs behind.
    _rounded_rect(cr, w, h, r)
    cr.set_source_rgba(20 / 255, 22 / 255, 30 / 255, 0.78)
    cr.fill()
    cr.save()
    _rounded_rect(cr, w, h, r)
    cr.clip()
    lg = cairo.LinearGradient(0, 0, 0, max(h, 1) * 0.42)
    lg.add_color_stop_rgba(0, 1, 1, 1, 0.08)
    lg.add_color_stop_rgba(1, 1, 1, 1, 0.0)
    cr.set_source(lg)
    cr.paint()
    cr.restore()
    _rounded_rect(cr, w, h, r)
    cr.set_source_rgba(*border)
    cr.set_line_width(1.0)
    cr.stroke()


def _set_classes(widget, *names):
    ctx = widget.get_style_context()
    for existing in list(ctx.list_classes()):
        if existing in names:
            continue
        if existing in ("start", "stop", "live", "running"):
            ctx.remove_class(existing)
    for name in names:
        ctx.add_class(name)


class TrackerWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Time Tracker")
        self.set_default_size(CARD_WIDTH, -1)
        self.set_size_request(CARD_WIDTH, -1)
        self.set_resizable(False)

        # Transparent background (rgba visual is an X11-only nicety; on
        # Wayland the compositor composites our alpha directly).
        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        # Layer-shell: BOTTOM layer → behind every window (tiled and
        # floating), above the wallpaper, on all workspaces. Anchored to
        # the top-left so the widget can be dragged anywhere via margins
        # (layer surfaces can't be moved by the compositor).
        GtkLayerShell.init_for_window(self)
        layer = GtkLayerShell.Layer.BOTTOM
        if os.environ.get("WIDGET_LAYER", "").lower() in ("top", "overlay"):
            layer = GtkLayerShell.Layer.OVERLAY
        GtkLayerShell.set_layer(self, layer)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, TOP_MARGIN)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, 0)
        GtkLayerShell.set_exclusive_zone(self, 0)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        # Drag-to-move state; restore a previously saved position if any
        self._drag = None
        self._top = TOP_MARGIN
        self._left = 0
        self._positioned = False
        pos = self._load_position()
        if pos is not None:
            self._top, self._left = pos
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, self._top)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, self._left)
            self._positioned = True
        self.connect("map", self._on_map)

        self.running = self._load_state()
        self.entries = _read_entries()
        self._heartbeat_mono = time.monotonic() if self.running else 0
        self._inhibit_fd = None
        self._inhibit_fdlist = None

        self._build_ui()
        self._update_ui()
        self._watch_shutdown()

        GLib.timeout_add_seconds(1, self._tick)

    # ── UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # EventBox paints the rounded card background (Gtk.Box can't in GTK3)
        card = Gtk.EventBox()
        card.set_visible_window(True)
        _add_class(card, "card")
        card.connect("draw", self._draw_card)
        self.card = card
        self.add(card)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(14)
        root.set_margin_end(14)
        card.add(root)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.dot = Gtk.Label(label="●")
        _add_class(self.dot, "accent-dot")
        self.dot.set_valign(Gtk.Align.CENTER)

        brand = Gtk.Label(label="TRACK")
        _add_class(brand, "brand")
        brand.set_halign(Gtk.Align.START)
        brand.set_hexpand(True)
        brand.set_xalign(0)

        self.today_btn = Gtk.MenuButton()
        _add_class(self.today_btn, "pill")
        self.today_btn.set_direction(Gtk.ArrowType.NONE)
        self.today_btn.set_tooltip_text("Today's sessions")
        self._build_popover()

        quit_btn = Gtk.Button(label="✕")
        _add_class(quit_btn, "quit")
        quit_btn.set_relief(Gtk.ReliefStyle.NONE)
        quit_btn.set_tooltip_text("Quit the widget (logs the running session)")
        quit_btn.connect("clicked", self._quit)

        header.pack_start(self.dot, False, False, 0)
        header.pack_start(brand, True, True, 0)
        header.pack_start(self.today_btn, False, False, 0)
        header.pack_start(quit_btn, False, False, 0)
        root.pack_start(header, False, False, 0)

        hair = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        _add_class(hair, "hairline")
        root.pack_start(hair, False, False, 0)

        self.entry = Gtk.Entry()
        _add_class(self.entry, "entry")
        self.entry.set_placeholder_text("What are you working on?")
        self.entry.set_tooltip_text("Enter to start or stop")
        self.entry.connect("activate", self._toggle)

        self.store = Gtk.ListStore.new([str])
        self.completion = Gtk.EntryCompletion()
        self.completion.set_model(self.store)
        self.completion.set_text_column(0)
        self.completion.set_minimum_key_length(0)
        self.completion.set_match_func(self._completion_match, None)
        self.entry.set_completion(self.completion)
        root.pack_start(self.entry, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.elapsed = Gtk.Label(label="0:00:00")
        _add_class(self.elapsed, "elapsed")
        self.elapsed.set_hexpand(True)
        self.elapsed.set_halign(Gtk.Align.START)
        self.elapsed.set_xalign(0)

        self.btn = Gtk.Button()
        self.btn.set_relief(Gtk.ReliefStyle.NONE)
        _add_class(self.btn, "play")
        self.btn.connect("clicked", self._toggle)
        row.pack_start(self.elapsed, True, True, 0)
        row.pack_start(self.btn, False, False, 0)
        root.pack_start(row, False, False, 0)

        # Drag-to-move: the card background and labels are the drag zone.
        # Presses on the entry/buttons never reach the card (they have their
        # own windows and consume their presses), so those still work.
        card.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
        )
        card.connect("button-press-event", self._drag_start)
        card.connect("motion-notify-event", self._drag_move)
        card.connect("button-release-event", self._drag_end)

        self.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
        )
        self.connect("motion-notify-event", self._drag_move)
        self.connect("button-release-event", self._drag_end)

        for w in (self.entry, self.btn, self.today_btn, quit_btn, self.dot, brand):
            w.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
            w.connect("motion-notify-event", self._drag_move)
            w.connect("button-release-event", self._drag_end)

    def _build_popover(self):
        popover = Gtk.Popover.new(self.today_btn)
        popover.set_size_request(260, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label="TODAY")
        _add_class(lbl, "brand")
        lbl.set_halign(Gtk.Align.START)
        lbl.set_hexpand(True)
        close = Gtk.Button(label="✕")
        _add_class(close, "quit")
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.set_tooltip_text("Close this panel")
        close.connect("clicked", lambda *_: popover.popdown())
        head.pack_start(lbl, True, True, 0)
        head.pack_start(close, False, False, 0)
        box.pack_start(head, False, False, 0)

        self.popover_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        open_log = Gtk.Button(label="Open log file")
        _add_class(open_log, "open-log")
        open_log.set_relief(Gtk.ReliefStyle.NONE)
        open_log.set_halign(Gtk.Align.START)
        open_log.set_tooltip_text(CSV_PATH)
        open_log.connect("clicked", self._open_log)

        box.pack_start(self.popover_list, False, False, 0)
        box.pack_start(open_log, False, False, 0)

        popover.add(box)
        box.show_all()
        self.today_btn.set_popover(popover)

    # ── State / storage ────────────────────────────────────────────────
    def _load_state(self):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError):
            return None
        if not state.get("task") or not state.get("start"):
            return None
        return _finish_if_rebooted(state)

    def _save_state(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = STATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.running, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, STATE_PATH)

    def _clear_state(self):
        try:
            os.remove(STATE_PATH)
        except OSError:
            pass

    def _append_entry(self, start_iso, end_iso, duration_sec, task):
        _write_entry(start_iso, end_iso, duration_sec, task)
        self.entries = _read_entries()

    def _watch_shutdown(self):
        # logind emits this while the session is still up, before SIGTERM.
        # A delay inhibitor keeps shutdown from killing us mid-write.
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        except GLib.Error:
            return
        self._sysbus = bus
        bus.signal_subscribe(
            "org.freedesktop.login1",
            "org.freedesktop.login1.Manager",
            "PrepareForShutdown",
            "/org/freedesktop/login1",
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_prepare_for_shutdown,
            None,
        )
        if self.running:
            self._take_shutdown_delay()

    def _on_prepare_for_shutdown(self, *args):
        params = next((a for a in args if isinstance(a, GLib.Variant)), None)
        if params is None:
            return
        try:
            active = params.get_child_value(0).get_boolean()
        except (AttributeError, TypeError):
            return
        if not active or not self.running:
            return
        self._stop()

    def _take_shutdown_delay(self):
        if self._inhibit_fdlist is not None:
            return
        bus = getattr(self, "_sysbus", None)
        if bus is None:
            return
        try:
            _res, fdlist = bus.call_with_unix_fd_list_sync(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                "Inhibit",
                GLib.Variant("(ssss)", (
                    "shutdown",
                    "timetracker",
                    "Stop the running task",
                    "delay",
                )),
                GLib.VariantType.new("(h)"),
                Gio.DBusCallFlags.NONE,
                3000,
                None,
                None,
            )
        except GLib.Error:
            return
        if fdlist is None:
            return
        try:
            fd = fdlist.get(0)
        except GLib.Error:
            return
        self._inhibit_fdlist = fdlist
        self._inhibit_fd = fd

    def _release_shutdown_delay(self):
        # UnixFDList.get() dups. The inhibitor stays until the list's own
        # fd is closed, which its finalizer does when we drop it.
        fd = self._inhibit_fd
        self._inhibit_fd = None
        self._inhibit_fdlist = None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass

    # ── Actions ────────────────────────────────────────────────────────
    def _toggle(self, *_):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        task = self.entry.get_text().strip() or "Untitled"
        now = datetime.now()
        stamp = now.isoformat(timespec="seconds")
        self.running = {
            "task": task,
            "start": stamp,
            "heartbeat": stamp,
        }
        self._heartbeat_mono = time.monotonic()
        self.entry.set_text(task)
        self._save_state()
        self._take_shutdown_delay()
        self._update_ui()

    def _stop(self):
        now = datetime.now()
        start = datetime.fromisoformat(self.running["start"])
        duration = (now - start).total_seconds()
        self._append_entry(
            self.running["start"],
            now.isoformat(timespec="seconds"),
            duration,
            self.running["task"],
        )
        self.running = None
        self._clear_state()
        self._release_shutdown_delay()
        self._update_ui()

    def _quit(self, *_):
        # Don't lose the running session: log it, then quit.
        if self.running:
            self._stop()
        app = self.get_application()
        self.destroy()
        if app is not None:
            app.quit()
        else:
            Gtk.main_quit()

    def _open_log(self, *_):
        try:
            subprocess.Popen(["xdg-open", CSV_PATH])
        except OSError:
            pass

    # ── Drag to move / position ───────────────────────────────────────
    def _load_position(self):
        try:
            with open(POS_PATH, encoding="utf-8") as f:
                p = json.load(f)
            return int(p["top"]), int(p["left"])
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return None

    def _save_position(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(POS_PATH, "w", encoding="utf-8") as f:
            json.dump({"top": self._top, "left": self._left}, f)

    def _on_map(self, *_):
        # First show: default to the old spot (right edge, below the waybar)
        if not self._positioned:
            win = self.get_window()
            if win is not None:
                mon = self.get_display().get_monitor_at_window(win).get_geometry()
                self._left = max(0, mon.width - self.get_allocated_width() - RIGHT_MARGIN)
                GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, self._left)
                self._positioned = True
        shot = os.environ.get("WIDGET_SHOT")
        if shot:
            GLib.timeout_add(250, self._dump_shot, shot)

    def _draw_card(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        if self.running:
            border = (166 / 255, 227 / 255, 161 / 255, 0.50)
        else:
            border = (122 / 255, 162 / 255, 247 / 255, 0.28)
        _draw_glass(cr, w, h, 18, border)
        return False

    def _dump_shot(self, path):
        win = self.get_window()
        if win is None:
            return False
        pb = Gdk.pixbuf_get_from_window(
            win, 0, 0, self.get_allocated_width(), self.get_allocated_height()
        )
        if pb is not None:
            pb.savev(path, "png", [], [])
        return False

    def _drag_start(self, widget, event):
        if event.button != 1 or self._drag:
            return False
        self._drag = (event.x_root, event.y_root, self._left, self._top)
        Gdk.pointer_grab(
            self.get_window(),
            False,
            Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK,
            None,
            None,
            event.time,
        )
        return True

    def _drag_move(self, widget, event):
        if not self._drag:
            return False
        sx, sy, oleft, otop = self._drag
        screen = self.get_screen()
        left = max(0, min(oleft + int(event.x_root - sx), max(0, screen.width() - 60)))
        top = max(0, min(otop + int(event.y_root - sy), max(0, screen.height() - 60)))
        self._left, self._top = left, top
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, left)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, top)
        return True

    def _drag_end(self, widget, event):
        if not self._drag:
            return False
        self._drag = None
        Gdk.pointer_ungrab(event.time)
        self._save_position()
        return True

    # ── UI updates ─────────────────────────────────────────────────────
    def _update_ui(self):
        if self.running:
            self.btn.set_label("■")
            self.btn.set_tooltip_text("Stop")
            _set_classes(self.btn, "play", "stop")
            _set_classes(self.dot, "accent-dot", "live")
            _set_classes(self.elapsed, "elapsed", "live")
            _set_classes(self.card, "card", "running")
            self.entry.set_sensitive(False)
            if not self.entry.get_text().strip():
                self.entry.set_text(self.running["task"])
            self._refresh_tasks([self.running["task"]] + _recent_tasks(self.entries))
        else:
            self.btn.set_label("▶")
            self.btn.set_tooltip_text("Start")
            _set_classes(self.btn, "play", "start")
            _set_classes(self.dot, "accent-dot")
            _set_classes(self.elapsed, "elapsed")
            _set_classes(self.card, "card")
            self.entry.set_sensitive(True)
            self._refresh_tasks(_recent_tasks(self.entries))

        self.card.queue_draw()
        self._tick()
        self._rebuild_today_list()

    def _today_label(self, live=0):
        total = _today_total(self.entries) + live
        if total <= 0 and not self.running:
            return "today"
        return _fmt_dur(total)

    def _rebuild_today_list(self):
        for child in list(self.popover_list.get_children()):
            self.popover_list.remove(child)

        today = date.today().isoformat()
        rows = [e for e in self.entries if e.get("start", "").startswith(today)]
        if self.running and self.running.get("start", "").startswith(today):
            live = {
                "task": self.running["task"],
                "duration_sec": str(
                    (datetime.now() - datetime.fromisoformat(self.running["start"])).total_seconds()
                ),
                "_live": True,
            }
            rows.append(live)

        if not rows:
            lbl = Gtk.Label(label="No sessions yet")
            _add_class(lbl, "empty")
            lbl.set_halign(Gtk.Align.START)
            self.popover_list.pack_start(lbl, False, False, 0)
            lbl.show()
            return

        for e in reversed(rows[-12:]):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            task = Gtk.Label(label=e.get("task", "?"))
            _add_class(task, "history-task")
            if e.get("_live"):
                _add_class(task, "live")
                task.set_text("●  " + (e.get("task") or "?"))
            task.set_hexpand(True)
            task.set_halign(Gtk.Align.START)
            task.set_xalign(0)
            task.set_ellipsize(Pango.EllipsizeMode.END)
            try:
                dur = float(e.get("duration_sec", 0))
            except (TypeError, ValueError):
                dur = 0
            t = Gtk.Label(label=_fmt_dur(dur) + (" ·" if e.get("_live") else ""))
            _add_class(t, "history-time")
            row.pack_start(task, True, True, 0)
            row.pack_start(t, False, False, 0)
            row.show_all()
            self.popover_list.pack_start(row, False, False, 0)

    def _refresh_tasks(self, tasks):
        self.store.clear()
        for t in tasks:
            self.store.append([t])

    def _maybe_heartbeat(self):
        if not self.running:
            return
        now_m = time.monotonic()
        if now_m - self._heartbeat_mono < 15:
            return
        self._heartbeat_mono = now_m
        self.running["heartbeat"] = datetime.now().isoformat(timespec="seconds")
        try:
            self._save_state()
        except OSError:
            pass

    def _tick(self):
        self._maybe_heartbeat()
        live = 0
        if self.running:
            start = datetime.fromisoformat(self.running["start"])
            live = (datetime.now() - start).total_seconds()
            self.elapsed.set_text(_fmt_clock(live))
        else:
            self.elapsed.set_text(_fmt_clock(0))
        self.today_btn.set_label(self._today_label(live))
        count = _today_count(self.entries) + (1 if self.running else 0)
        self.today_btn.set_tooltip_text(f"{count} session{'s' if count != 1 else ''} today")
        return True

    def _completion_match(self, completion, key, it, user_data):
        return key.strip().lower() in self.store[it][0].lower()


class TrackerApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.win = None

    def do_activate(self):
        if not self.win:
            self.win = TrackerWindow(application=self)
        self.win.show_all()


def _acquire_single_instance():
    """Exit silently if another instance is already running (flock guard).

    Makes SUPER+SHIFT+T a safe "bring it back" key: a no-op while the
    widget is running, a fresh launch after it was quit.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    lock = open(os.path.join(DATA_DIR, "widget.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(0)
    return lock


def main():
    global _LOCK
    _LOCK = _acquire_single_instance()
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    app = TrackerApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
