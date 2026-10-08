#!/usr/bin/env python3
"""
Tasks — desktop widget for Hyprland, matching the time-tracker widget.

A small widget drawn in the Wayland *bottom* layer (via gtk-layer-shell),
so it sits behind every window — tiled and floating — like a Conky-style
desktop widget. It shows on all workspaces and defaults to the top-left,
just below the waybar (the time tracker lives on the right); drag it
anywhere with the mouse and the position is remembered.

Type a task, hit Enter or Add. Check it off when done, ✕ to delete.
Prefix with ! for high priority. Completed tasks live in the header
popover; undo from there.

    ~/.local/share/taskwidget/tasks.json

SUPER+SHIFT+K brings the widget back up after it was quit.
"""

import fcntl
import json
import math
import os
import subprocess
import sys
import uuid
from datetime import date, datetime

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GLib, Gtk, GtkLayerShell, Pango
import cairo

APP_ID = "dev.taskwidget"
DATA_DIR = os.path.expanduser("~/.local/share/taskwidget")
TASKS_PATH = os.path.join(DATA_DIR, "tasks.json")
POS_PATH = os.path.join(DATA_DIR, "position.json")

# Opposite corner from the time tracker (top-right).
TOP_MARGIN = 8
LEFT_MARGIN = 16
LIST_MAX_HEIGHT = 280
CARD_WIDTH = 300

# Glass Tokyo-Night / Catppuccin, matching rofi + dunst.
CSS = b"""
@define-color bg rgba(20, 22, 30, 0.01);
@define-color fg #e0e6f0;
@define-color muted #a9b1d6;
@define-color subtle #565f89;
@define-color overlay rgba(255, 255, 255, 0.06);
@define-color accent #cba6f7;
@define-color blue #7aa2f7;
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

.accent-dot { color: @accent; font-size: 10px; }
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
  background-color: rgba(203, 166, 247, 0.18);
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
  background-color: rgba(203, 166, 247, 0.30);
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
.entry:focus { border-color: rgba(203, 166, 247, 0.55); }

button.add {
  min-width: 38px;
  min-height: 38px;
  border-radius: 999px;
  background: @green;
  color: @surface;
  font-size: 20px;
  font-weight: 700;
}
button.add:hover { background: @teal; }

.task-row { border-radius: 10px; padding: 0; }
.task-row:hover { background: rgba(255, 255, 255, 0.045); }
.task-row.high { background: rgba(250, 179, 135, 0.08); }
.task-row.high:hover { background: rgba(250, 179, 135, 0.14); }

button.check {
  min-width: 22px;
  min-height: 22px;
  border-radius: 999px;
  padding: 0;
  margin: 0;
  font-size: 15px;
  color: #7f849c;
}
button.check:hover { color: @green; background: rgba(166, 227, 161, 0.12); }

.task-title { color: @fg; font-size: 13px; }
.task-title.high { color: @peach; font-weight: 700; }

.empty { color: @subtle; font-size: 12px; }
.history-task { color: @fg; font-size: 12px; }
.history-task.done { color: #6c7086; }
.history-time { color: @muted; font-size: 11px; font-feature-settings: "tnum"; }

button.undo {
  background: transparent;
  color: @blue;
  font-size: 11px;
  border-radius: 8px;
  padding: 2px 7px;
}
button.undo:hover { background: rgba(122, 162, 247, 0.16); color: @fg; }

popover {
  background: @surface;
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 12px;
}
button.open-log {
  background: transparent;
  color: @blue;
  font-size: 11px;
  border-radius: 8px;
  padding: 4px 8px;
}
button.open-log:hover { background: rgba(255, 255, 255, 0.08); color: @fg; }

scrollbar { background: transparent; border: none; }
scrollbar slider {
  background: rgba(255, 255, 255, 0.16);
  border-radius: 4px;
  min-width: 5px;
  min-height: 5px;
}
scrollbar slider:hover { background: rgba(255, 255, 255, 0.28); }
"""

_LOCK = None


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


def _write_json(path, data):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _load_tasks():
    try:
        with open(TASKS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        tasks = data.get("tasks", data if isinstance(data, list) else [])
        return [t for t in tasks if isinstance(t, dict) and t.get("title")]
    except (OSError, json.JSONDecodeError, TypeError):
        return []


def _display_title(title):
    t = (title or "").strip()
    if t.startswith("!"):
        return t[1:].lstrip() or t, True
    return t, False


def _fmt_when(iso):
    try:
        dt = datetime.fromisoformat(iso)
    except (TypeError, ValueError):
        return ""
    if dt.date() == date.today():
        return dt.strftime("%H:%M")
    return dt.strftime("%b %d")


class TaskWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("Tasks")
        self.set_default_size(CARD_WIDTH, -1)
        self.set_size_request(CARD_WIDTH, -1)
        self.set_resizable(False)

        self.set_app_paintable(True)
        visual = self.get_screen().get_rgba_visual()
        if visual is not None:
            self.set_visual(visual)

        GtkLayerShell.init_for_window(self)
        layer = GtkLayerShell.Layer.BOTTOM
        if os.environ.get("WIDGET_LAYER", "").lower() in ("top", "overlay"):
            layer = GtkLayerShell.Layer.OVERLAY
        GtkLayerShell.set_layer(self, layer)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_anchor(self, GtkLayerShell.Edge.LEFT, True)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, TOP_MARGIN)
        GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, LEFT_MARGIN)
        GtkLayerShell.set_exclusive_zone(self, 0)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.ON_DEMAND)

        self._drag = None
        self._top = TOP_MARGIN
        self._left = LEFT_MARGIN
        self._positioned = False
        self._editing_id = None
        pos = self._load_position()
        if pos is not None:
            self._top, self._left = pos
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.TOP, self._top)
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, self._left)
            self._positioned = True
        self.connect("map", self._on_map)

        self.tasks = _load_tasks()
        if os.environ.get("WIDGET_DEMO") == "1" and not self.tasks:
            now = datetime.now().isoformat(timespec="seconds")
            self.tasks = [
                {"id": "demo1", "title": "Review open PRs", "done": False, "created": now, "completed": None},
                {"id": "demo2", "title": "! Deploy staging", "done": False, "created": now, "completed": None},
                {"id": "demo3", "title": "Inbox zero", "done": False, "created": now, "completed": None},
            ]
        self._build_ui()
        self._refresh()

    # ── UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        card = Gtk.EventBox()
        card.set_visible_window(True)
        _add_class(card, "card")
        card.connect("draw", self._draw_card)
        self.add(card)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(14)
        root.set_margin_end(14)
        card.add(root)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dot = Gtk.Label(label="●")
        _add_class(dot, "accent-dot")
        brand = Gtk.Label(label="TASKS")
        _add_class(brand, "brand")
        brand.set_halign(Gtk.Align.START)
        brand.set_hexpand(True)
        brand.set_xalign(0)

        self.done_btn = Gtk.MenuButton()
        _add_class(self.done_btn, "pill")
        self.done_btn.set_direction(Gtk.ArrowType.NONE)
        self.done_btn.set_tooltip_text("Completed tasks")
        self._build_popover()

        quit_btn = Gtk.Button(label="✕")
        _add_class(quit_btn, "quit")
        quit_btn.set_relief(Gtk.ReliefStyle.NONE)
        quit_btn.set_tooltip_text("Quit the widget (tasks stay saved)")
        quit_btn.connect("clicked", self._quit)

        header.pack_start(dot, False, False, 0)
        header.pack_start(brand, True, True, 0)
        header.pack_start(self.done_btn, False, False, 0)
        header.pack_start(quit_btn, False, False, 0)
        root.pack_start(header, False, False, 0)

        hair = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        _add_class(hair, "hairline")
        root.pack_start(hair, False, False, 0)

        add_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.entry = Gtk.Entry()
        _add_class(self.entry, "entry")
        self.entry.set_placeholder_text("What needs doing?")
        self.entry.set_tooltip_text("Enter to add. Prefix with ! for high priority.")
        self.entry.connect("activate", self._add_task)
        add_btn = Gtk.Button(label="+")
        _add_class(add_btn, "add")
        add_btn.set_relief(Gtk.ReliefStyle.NONE)
        add_btn.set_tooltip_text("Add task")
        add_btn.connect("clicked", self._add_task)
        add_row.pack_start(self.entry, True, True, 0)
        add_row.pack_start(add_btn, False, False, 0)
        root.pack_start(add_row, False, False, 0)

        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_propagate_natural_height(True)
        self.scroll.set_max_content_height(LIST_MAX_HEIGHT)
        self.task_list = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.scroll.add(self.task_list)
        root.pack_start(self.scroll, False, False, 0)

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

        for w in (self.entry, add_btn, self.done_btn, quit_btn, dot, brand):
            w.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
            w.connect("motion-notify-event", self._drag_move)
            w.connect("button-release-event", self._drag_end)

        self._add_btn = add_btn
        self._quit_btn = quit_btn

    def _build_popover(self):
        popover = Gtk.Popover.new(self.done_btn)
        popover.set_size_request(260, -1)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(12)
        box.set_margin_end(12)

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label="DONE")
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
        box.pack_start(self.popover_list, False, False, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        open_log = Gtk.Button(label="Open file")
        _add_class(open_log, "open-log")
        open_log.set_relief(Gtk.ReliefStyle.NONE)
        open_log.set_halign(Gtk.Align.START)
        open_log.set_tooltip_text(TASKS_PATH)
        open_log.connect("clicked", self._open_log)
        clear_done = Gtk.Button(label="Clear")
        _add_class(clear_done, "open-log")
        clear_done.set_relief(Gtk.ReliefStyle.NONE)
        clear_done.set_tooltip_text("Delete all completed tasks")
        clear_done.connect("clicked", self._clear_done)
        actions.pack_start(open_log, False, False, 0)
        actions.pack_end(clear_done, False, False, 0)
        box.pack_start(actions, False, False, 0)

        popover.add(box)
        box.show_all()
        self.done_btn.set_popover(popover)

    # ── Storage ────────────────────────────────────────────────────────
    def _save(self):
        _write_json(TASKS_PATH, {"tasks": self.tasks})

    def _find(self, task_id):
        for t in self.tasks:
            if t.get("id") == task_id:
                return t
        return None

    # ── Actions ────────────────────────────────────────────────────────
    def _add_task(self, *_):
        title = self.entry.get_text().strip()
        if not title:
            return
        self.tasks.insert(0, {
            "id": uuid.uuid4().hex[:12],
            "title": title,
            "done": False,
            "created": datetime.now().isoformat(timespec="seconds"),
            "completed": None,
        })
        self.entry.set_text("")
        self._save()
        self._refresh()
        self.entry.grab_focus()

    def _complete(self, task_id):
        task = self._find(task_id)
        if not task or task.get("done"):
            return
        task["done"] = True
        task["completed"] = datetime.now().isoformat(timespec="seconds")
        if self._editing_id == task_id:
            self._editing_id = None
        self._save()
        self._refresh()

    def _undo(self, task_id):
        task = self._find(task_id)
        if not task or not task.get("done"):
            return
        task["done"] = False
        task["completed"] = None
        self._save()
        self._refresh()

    def _delete(self, task_id):
        if self._editing_id == task_id:
            self._editing_id = None
        self.tasks = [t for t in self.tasks if t.get("id") != task_id]
        self._save()
        self._refresh()

    def _clear_done(self, *_):
        self.tasks = [t for t in self.tasks if not t.get("done")]
        self._save()
        self._refresh()

    def _commit_edit(self, task_id, entry):
        if self._editing_id != task_id:
            return
        title = entry.get_text().strip()
        task = self._find(task_id)
        self._editing_id = None
        if task and title:
            task["title"] = title
            self._save()
        self._refresh()

    def _quit(self, *_):
        app = self.get_application()
        self.destroy()
        if app is not None:
            app.quit()
        else:
            Gtk.main_quit()

    def _open_log(self, *_):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(TASKS_PATH):
            self._save()
        try:
            subprocess.Popen(["xdg-open", TASKS_PATH])
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
        _write_json(POS_PATH, {"top": self._top, "left": self._left})

    def _on_map(self, *_):
        if not self._positioned:
            GtkLayerShell.set_margin(self, GtkLayerShell.Edge.LEFT, LEFT_MARGIN)
            self._left = LEFT_MARGIN
            self._positioned = True
        shot = os.environ.get("WIDGET_SHOT")
        if shot:
            GLib.timeout_add(250, self._dump_shot, shot)

    def _draw_card(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        _draw_glass(cr, w, h, 18, (203 / 255, 166 / 255, 247 / 255, 0.28))
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

    # ── Render ─────────────────────────────────────────────────────────
    def _refresh(self):
        open_tasks = [t for t in self.tasks if not t.get("done")]
        done_tasks = sorted(
            (t for t in self.tasks if t.get("done")),
            key=lambda t: t.get("completed") or "",
            reverse=True,
        )
        n_open, n_done = len(open_tasks), len(done_tasks)
        if n_open:
            self.done_btn.set_label(str(n_open))
        else:
            self.done_btn.set_label("0")
        self.done_btn.set_tooltip_text(f"{n_open} open · {n_done} done")
        self._render_open(open_tasks)
        self._render_done(done_tasks)

    def _render_open(self, open_tasks):
        for child in list(self.task_list.get_children()):
            self.task_list.remove(child)

        if not open_tasks:
            lbl = Gtk.Label(label="Nothing queued")
            _add_class(lbl, "empty")
            lbl.set_halign(Gtk.Align.START)
            lbl.set_margin_top(6)
            lbl.set_margin_bottom(2)
            self.task_list.pack_start(lbl, False, False, 0)
            self.task_list.show_all()
            return

        for task in open_tasks:
            self.task_list.pack_start(self._open_row(task), False, False, 0)
        self.task_list.show_all()

        if self._editing_id:
            for child in self.task_list.get_children():
                edit = getattr(child, "_edit_entry", None)
                if edit is not None:
                    edit.grab_focus()
                    edit.set_position(-1)
                    break

    def _open_row(self, task):
        task_id = task["id"]
        text, high = _display_title(task.get("title", ""))
        row = Gtk.EventBox()
        _add_class(row, "task-row")
        if high:
            _add_class(row, "high")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_margin_start(4)
        box.set_margin_end(2)
        row.add(box)

        check = Gtk.Button(label="○")
        _add_class(check, "check")
        check.set_relief(Gtk.ReliefStyle.NONE)
        check.set_tooltip_text("Mark done")
        check.connect("clicked", lambda *_: self._complete(task_id))
        check.connect("enter-notify-event", lambda b, *_: (b.set_label("✓") or False))
        check.connect("leave-notify-event", lambda b, *_: (b.set_label("○") or False))
        box.pack_start(check, False, False, 0)

        if self._editing_id == task_id:
            edit = Gtk.Entry()
            _add_class(edit, "entry")
            edit.set_text(task.get("title", ""))
            edit.connect("activate", lambda e: self._commit_edit(task_id, e))
            edit.connect(
                "focus-out-event",
                lambda e, _: (self._commit_edit(task_id, e) or False),
            )
            edit.connect("key-press-event", self._edit_key)
            box.pack_start(edit, True, True, 0)
            row._edit_entry = edit
        else:
            title = Gtk.Label(label=text)
            _add_class(title, "task-title")
            if high:
                _add_class(title, "high")
            title.set_halign(Gtk.Align.START)
            title.set_hexpand(True)
            title.set_ellipsize(Pango.EllipsizeMode.END)
            title.set_xalign(0)
            title.set_tooltip_text("Double-click to edit")
            wrap = Gtk.EventBox()
            wrap.add(title)
            wrap.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
            wrap.connect("button-press-event", self._on_title_press, task_id)
            box.pack_start(wrap, True, True, 0)

        delete = Gtk.Button(label="✕")
        _add_class(delete, "quit")
        delete.set_relief(Gtk.ReliefStyle.NONE)
        delete.set_tooltip_text("Delete task")
        delete.set_opacity(0.28)
        delete.connect("clicked", lambda *_: self._delete(task_id))
        box.pack_start(delete, False, False, 0)

        row.connect("enter-notify-event", lambda *_: (delete.set_opacity(1) or False))
        row.connect("leave-notify-event", lambda *_: (delete.set_opacity(0.28) or False))

        for w in (check, delete):
            w.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
            w.connect("motion-notify-event", self._drag_move)
            w.connect("button-release-event", self._drag_end)
        return row

    def _on_title_press(self, widget, event, task_id):
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == 1:
            self._editing_id = task_id
            self._refresh()
            return True
        return False

    def _edit_key(self, entry, event):
        if event.keyval == Gdk.KEY_Escape:
            self._editing_id = None
            self._refresh()
            return True
        return False

    def _render_done(self, done_tasks):
        for child in list(self.popover_list.get_children()):
            self.popover_list.remove(child)

        if not done_tasks:
            lbl = Gtk.Label(label="Nothing done yet")
            _add_class(lbl, "empty")
            lbl.set_halign(Gtk.Align.START)
            self.popover_list.pack_start(lbl, False, False, 0)
            lbl.show()
            return

        for task in done_tasks[:20]:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            text, _high = _display_title(task.get("title", "?"))
            title = Gtk.Label(label=text)
            _add_class(title, "history-task")
            _add_class(title, "done")
            title.set_hexpand(True)
            title.set_halign(Gtk.Align.START)
            title.set_xalign(0)
            title.set_ellipsize(Pango.EllipsizeMode.END)
            when = Gtk.Label(label=_fmt_when(task.get("completed")))
            _add_class(when, "history-time")
            undo = Gtk.Button(label="undo")
            _add_class(undo, "undo")
            undo.set_relief(Gtk.ReliefStyle.NONE)
            undo.set_tooltip_text("Move back to open")
            task_id = task["id"]
            undo.connect("clicked", lambda _b, i=task_id: self._undo(i))
            row.pack_start(title, True, True, 0)
            row.pack_start(when, False, False, 0)
            row.pack_start(undo, False, False, 0)
            row.show_all()
            self.popover_list.pack_start(row, False, False, 0)


class TaskApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID)
        self.win = None

    def do_activate(self):
        if not self.win:
            self.win = TaskWindow(application=self)
        self.win.show_all()


def _acquire_single_instance():
    """Exit silently if another instance is already running (flock guard).

    Makes SUPER+SHIFT+K a safe "bring it back" key: a no-op while the
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
    app = TaskApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
