"""
Глобальные горячие клавиши Ctrl+C/V/X/A, работающие вне зависимости от раскладки
(по аппаратным скан-кодам Windows).
"""

import ctypes
import tkinter as tk


SCAN_A = 0x1E
SCAN_C = 0x2E
SCAN_V = 0x2F
SCAN_X = 0x2D


def _get_scan_code(event):
    try:
        return ctypes.windll.user32.MapVirtualKeyW(event.keycode, 0)
    except Exception:
        return event.keycode


def install_keyboard_shortcuts(root):
    def on_ctrl_key(event):
        if not (event.state & 0x4):
            return
        if event.keysym in ("c", "C", "v", "V", "x", "X", "a", "A"):
            return
        sc = _get_scan_code(event)
        w = event.widget
        if sc == SCAN_C:
            return _do_copy(w)
        if sc == SCAN_V:
            return _do_paste(w)
        if sc == SCAN_X:
            return _do_cut(w)
        if sc == SCAN_A:
            return _do_select_all(w)

    root.bind_all("<Control-KeyPress>", on_ctrl_key, add="+")


def _do_copy(widget):
    try:
        if isinstance(widget, tk.Text):
            text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            text = widget.selection_get()
        widget.clipboard_clear()
        widget.clipboard_append(text)
    except tk.TclError:
        pass
    return "break"


def _do_cut(widget):
    try:
        if isinstance(widget, tk.Text) and str(widget.cget("state")) == "disabled":
            return "break"
        if isinstance(widget, tk.Text):
            text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        else:
            text = widget.selection_get()
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
    except tk.TclError:
        pass
    return "break"


def _do_paste(widget):
    if isinstance(widget, tk.Text) and str(widget.cget("state")) == "disabled":
        return "break"
    try:
        text = widget.clipboard_get()
    except tk.TclError:
        return "break"
    try:
        if isinstance(widget, tk.Text):
            try:
                if widget.tag_ranges(tk.SEL):
                    widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            widget.insert(tk.INSERT, text)
        else:
            try:
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            widget.insert(tk.INSERT, text)
    except tk.TclError:
        pass
    return "break"


def _do_select_all(widget):
    try:
        if isinstance(widget, tk.Text):
            widget.tag_add(tk.SEL, "1.0", tk.END)
            widget.mark_set(tk.INSERT, "1.0")
            widget.see(tk.INSERT)
        else:
            widget.selection_range(0, tk.END)
            widget.icursor(tk.END)
    except tk.TclError:
        pass
    return "break"