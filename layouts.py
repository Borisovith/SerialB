"""
Только интерфейс главного окна: сетка, расположение, дизайн.
Никакой логики — все действия делегируются в app (обработчики).
"""

import tkinter as tk
from tkinter import ttk

from monitor_config import Localization


_IS_DARK = True


def set_theme_mode(is_dark):
    global _IS_DARK
    _IS_DARK = bool(is_dark)


def P(app, key):
    return app.palette.get(key, "#000000")


# ─────────────────────── ХЕЛПЕРЫ ЦВЕТА/КНОПОК ───────────────────────

def _auto_fg(bg_hex):
    """Автоконтраст: тёмный текст на светлом фоне, светлый — на тёмном."""
    try:
        bg_hex = bg_hex.lstrip("#")
        r = int(bg_hex[0:2], 16)
        g = int(bg_hex[2:4], 16)
        b = int(bg_hex[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#1e1e1e" if brightness > 140 else "#ffffff"
    except Exception:
        return "#ffffff"


def _hover_color(hex_color, is_dark=True):
    factor = 1.25 if is_dark else 0.85
    try:
        hex_color = hex_color.lstrip("#")
        r = max(0, min(255, int(int(hex_color[0:2], 16) * factor)))
        g = max(0, min(255, int(int(hex_color[2:4], 16) * factor)))
        b = max(0, min(255, int(int(hex_color[4:6], 16) * factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def _btn(parent, text, bg, fg=None, **kw):
    """Создаёт tk.Button с авто-контрастным цветом текста."""
    if fg is None:
        fg = _auto_fg(bg)
    return tk.Button(parent, text=text, bg=bg, fg=fg, bd=0, **kw)


# ─────────────────────── СБОРКА ───────────────────────

def build_main_ui(app):
    _build_top_bar(app)
    _build_macro_bar(app)
    _build_side_panel(app)
    _build_bottom_bar(app)
    _build_log_area(app)

    attach_hover_all(app.root)

    refresh_macro_buttons(app)
    set_scroll_state(app)
    set_time_state(app)
    set_delta_state(app)
    update_connection_indicator(app, connected=False)
    update_autoconnect_indicator(app)
    update_line_counter(app)


# ─────────────────────── HOVER ───────────────────────

def _bind_hover(widget):
    widget._normal_bg = widget.cget("bg")
    widget._normal_fg = widget.cget("fg")
    widget._hover_bg = _hover_color(widget._normal_bg, _IS_DARK)
    widget._hovered = False

    def _mouse_inside():
        try:
            x, y = widget.winfo_pointerxy()
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            ww = widget.winfo_width()
            wh = widget.winfo_height()
            return wx <= x < wx + ww and wy <= y < wy + wh
        except Exception:
            return False

    def on_enter(_):
        if str(widget.cget("state")) == "disabled":
            return
        if not _mouse_inside():
            return
        widget._hovered = True
        widget.config(bg=widget._hover_bg)

    def on_leave(_):
        if _mouse_inside():
            return
        widget._hovered = False
        widget.config(bg=widget._normal_bg)

    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", on_leave, add="+")


def attach_hover_all(root):
    def walk(w):
        for child in w.winfo_children():
            if isinstance(child, tk.Button):
                _bind_hover(child)
            walk(child)
    walk(root)


def set_button_colors(btn, bg, fg=None):
    btn._normal_bg = bg
    btn._hover_bg = _hover_color(bg, _IS_DARK)
    if not hasattr(btn, "_hovered"):
        btn._hovered = False

    if fg is None:
        fg = _auto_fg(bg)
    btn._normal_fg = fg

    if btn._hovered and str(btn.cget("state")) != "disabled":
        btn.config(bg=btn._hover_bg, fg=fg)
    else:
        btn.config(bg=bg, fg=fg)


# ─────────────────────── TOP ───────────────────────

def _build_top_bar(app):
    top = tk.Frame(app.root, bg=P(app, "bg_panel"))
    top.pack(fill=tk.X, side=tk.TOP, pady=5, padx=5)

    ttk.Label(top, text=Localization.get("port_select"),
              background=P(app, "bg_panel"),
              foreground=P(app, "fg_text")).pack(side=tk.LEFT, padx=5)

    app.port_combo = ttk.Combobox(top, width=12, state="readonly")
    app.port_combo.pack(side=tk.LEFT, padx=5)

    ttk.Button(top, text=Localization.get("refresh"),
               command=app.refresh_ports).pack(side=tk.LEFT, padx=5)

    ttk.Label(top, text=Localization.get("baudrate"),
              background=P(app, "bg_panel"),
              foreground=P(app, "fg_text")).pack(side=tk.LEFT, padx=5)

    baud_list = ["300", "1200", "2400", "4800", "9600", "19200", "38400",
                 "57600", "74880", "115200", "230400", "460800", "500000",
                 "921600", "1000000", "2000000"]
    app.baud_combo = ttk.Combobox(top, width=10, values=baud_list)
    app.baud_combo.set("115200")
    app.baud_combo.pack(side=tk.LEFT, padx=5)

    app.conn_btn = _btn(top, Localization.get("connect"), P(app, "primary"),
                        padx=8, pady=2, command=app.press_connect)
    app.conn_btn.pack(side=tk.LEFT, padx=5)

    app.disconn_btn = _btn(top, Localization.get("disconnect"), P(app, "neutral"),
                           padx=8, pady=2, state=tk.DISABLED,
                           command=app.press_disconnect)
    app.disconn_btn.pack(side=tk.LEFT, padx=5)

    ind_frame = tk.Frame(top, bg=P(app, "bg_panel"))
    ind_frame.pack(side=tk.LEFT, padx=(10, 0))

    app.conn_indicator = tk.Canvas(ind_frame, width=14, height=14,
                                   bg=P(app, "bg_panel"), highlightthickness=0)
    app.conn_indicator.pack(side=tk.LEFT, padx=(0, 4))
    app.conn_indicator_circle = app.conn_indicator.create_oval(
        2, 2, 12, 12, fill=P(app, "ind_grey"), outline="")

    app.conn_indicator_label = tk.Label(
        ind_frame, text=Localization.get("conn_state_disconnected", "Offline"),
        bg=P(app, "bg_panel"), fg=P(app, "fg_disabled"),
        font=("Segoe UI", 8, "bold"))
    app.conn_indicator_label.pack(side=tk.LEFT)

    app.reset_var = tk.BooleanVar(value=True)
    tk.Checkbutton(top, text=Localization.get("reset_on_conn"), variable=app.reset_var,
                   bg=P(app, "bg_panel"), fg=P(app, "fg_text"),
                   selectcolor=P(app, "bg_widget"),
                   activebackground=P(app, "bg_panel"),
                   activeforeground=P(app, "fg_accent")
                   ).pack(side=tk.LEFT, padx=3)

    app.auto_conn_var = tk.BooleanVar(value=False)
    app.auto_conn_chk = tk.Checkbutton(
        top, text=Localization.get("auto_conn"), variable=app.auto_conn_var,
        bg=P(app, "bg_panel"), fg=P(app, "fg_text"),
        selectcolor=P(app, "bg_widget"),
        activebackground=P(app, "bg_panel"),
        activeforeground=P(app, "fg_accent"),
        command=app.on_autoconnect_toggle)
    app.auto_conn_chk.pack(side=tk.LEFT, padx=3)

    timeout_frame = tk.Frame(top, bg=P(app, "bg_panel"))
    timeout_frame.pack(side=tk.LEFT, padx=10)

    ttk.Label(timeout_frame, text=Localization.get("timeout_label"),
              background=P(app, "bg_panel"),
              foreground=P(app, "fg_accent"),
              font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=2)

    slider_row = tk.Frame(timeout_frame, bg=P(app, "bg_panel"))
    slider_row.pack(anchor="w")

    _initial_timeout = int(getattr(app.backend, "timeout_ms", 50))

    app.timeout_scale = tk.Scale(slider_row, from_=1, to=500, orient=tk.HORIZONTAL,
                                 bg=P(app, "bg_panel"), fg=P(app, "fg_accent"),
                                 bd=0, highlightthickness=0, width=10, length=100,
                                 font=("Consolas", 8), command=app.on_scale_move)
    if _initial_timeout <= 500:
        app.timeout_scale.set(_initial_timeout)
    else:
        app.timeout_scale.set(500)
    app.timeout_scale.pack(side=tk.LEFT, padx=2)

    app.timeout_entry = tk.Entry(slider_row, bg=P(app, "bg_widget"),
                                 fg=P(app, "fg_accent"),
                                 insertbackground=P(app, "fg_text"), bd=1,
                                 font=("Consolas", 10, "bold"), width=5,
                                 justify=tk.CENTER)
    app.timeout_entry.insert(0, str(_initial_timeout))
    app.timeout_entry.pack(side=tk.LEFT, padx=2)
    app.timeout_entry.bind("<Return>", lambda e: app.on_entry_type())

    ttk.Label(slider_row, text=Localization.get("ms"),
              background=P(app, "bg_panel"),
              foreground=P(app, "fg_accent"),
              font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=1)


# ─────────────────────── MACROS ───────────────────────

def _build_macro_bar(app):
    macro_frame = tk.Frame(app.root, bg=P(app, "bg_panel"))
    macro_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 5), padx=5)

    ttk.Label(macro_frame, text=Localization.get("macros_header"),
              background=P(app, "bg_panel"),
              foreground=P(app, "fg_accent"),
              font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)

    app.macros_container = tk.Frame(macro_frame, bg=P(app, "bg_panel"))
    app.macros_container.pack(side=tk.LEFT, padx=5)

    for i in range(6):
        name_e = tk.Entry(app.root)
        cmd_e = tk.Entry(app.root)
        app.macro_entries.append((name_e, cmd_e))
        btn = _btn(app.macros_container,
                   f"{Localization.get('macro_default')} {i+1}",
                   P(app, "idle"), padx=6, pady=2,
                   command=lambda idx=i: app.run_macro(idx))
        btn.pack(side=tk.LEFT, padx=3)
        app.macro_buttons.append(btn)

    _btn(macro_frame, Localization.get("settings_btn"), P(app, "primary"),
         padx=10, pady=2,
         command=app.open_settings_window).pack(side=tk.RIGHT, padx=5)


# ─────────────────────── SIDE ───────────────────────

def _build_side_panel(app):
    side = tk.Frame(app.root, bg=P(app, "bg_root"), width=160)
    side.pack(fill=tk.Y, side=tk.LEFT, padx=5, pady=5)

    app.scroll_btn = _btn(side, Localization.get("freeze_screen"),
                          P(app, "idle"), padx=6, pady=4, anchor="w",
                          command=app.toggle_scroll)
    app.scroll_btn.pack(fill=tk.X, pady=3)

    app.rx_chk = tk.Checkbutton(side, text=Localization.get("show_rx"),
                                variable=app.show_rx,
                                command=app.rebuild_log_view,
                                bg=P(app, "bg_root"),
                                fg=P(app, "fg_accent"),
                                selectcolor=P(app, "bg_panel"),
                                activebackground=P(app, "bg_root"),
                                activeforeground=P(app, "fg_accent"),
                                anchor="w", font=("Segoe UI", 9, "bold"))
    app.rx_chk.pack(fill=tk.X, pady=3)

    app.tx_chk = tk.Checkbutton(side, text=Localization.get("show_tx"),
                                variable=app.show_tx,
                                command=app.rebuild_log_view,
                                bg=P(app, "bg_root"),
                                fg=P(app, "fg_tx"),
                                selectcolor=P(app, "bg_panel"),
                                activebackground=P(app, "bg_root"),
                                activeforeground=P(app, "fg_tx"),
                                anchor="w", font=("Segoe UI", 9, "bold"))
    app.tx_chk.pack(fill=tk.X, pady=3)

    _btn(side, Localization.get("clear_log"), P(app, "idle"),
         padx=6, pady=4, anchor="w",
         command=app.clear_log).pack(fill=tk.X, pady=3)

    _btn(side, Localization.get("reset_esp"), P(app, "idle"),
         padx=6, pady=4, anchor="w",
         command=app.backend.reset_esp).pack(fill=tk.X, pady=3)

    app.time_btn = _btn(side, Localization.get("time_on"), P(app, "success"),
                        padx=6, pady=4, anchor="w",
                        command=app.toggle_time)
    app.time_btn.pack(fill=tk.X, pady=3)

    app.delta_btn = _btn(side, Localization.get("delta_off"), P(app, "idle"),
                         padx=6, pady=4, anchor="w",
                         command=app.toggle_delta)
    app.delta_btn.pack(fill=tk.X, pady=3)

    app.copy_btn = _btn(side, Localization.get("to_clipboard"), P(app, "idle"),
                        padx=6, pady=4, anchor="w",
                        command=app.copy_clipboard)
    app.copy_btn.pack(fill=tk.X, pady=3)

    _btn(side, Localization.get("to_file"), P(app, "idle"),
         padx=6, pady=4, anchor="w",
         command=lambda: _save_file(app)).pack(fill=tk.X, pady=3)

    counter_frame = tk.Frame(side, bg=P(app, "bg_root"))
    counter_frame.pack(fill=tk.X, pady=(15, 0))

    app.line_counter_label = tk.Label(
        counter_frame, text="", bg=P(app, "bg_root"), fg=P(app, "fg_muted"),
        font=("Consolas", 8), anchor="w", justify="left", cursor="hand2")
    app.line_counter_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    app.line_counter_label.bind("<Button-1>", lambda e: app.open_settings_on_general())

    app.max_lines_btn = tk.Button(
        counter_frame, text="⚙",
        bg=P(app, "bg_root"), fg=P(app, "fg_muted"),
        bd=0, padx=2, pady=0,
        activebackground=P(app, "bg_root"),
        activeforeground=P(app, "fg_accent"),
        font=("Segoe UI", 9, "bold"), cursor="hand2",
        command=app.open_settings_on_general)
    app.max_lines_btn.pack(side=tk.RIGHT)


def _save_file(app):
    from monitor_config import MonitorConfig
    MonitorConfig.save_file(app)


# ─────────────────────── BOTTOM ───────────────────────

def _build_bottom_bar(app):
    bot_frame = tk.Frame(app.root, bg=P(app, "bg_panel"))
    bot_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5, padx=5)
    bot_frame.grid_columnconfigure(1, weight=1)

    tk.Label(bot_frame, text=Localization.get("search_lbl"),
             background=P(app, "bg_panel"), foreground=P(app, "fg_accent"),
             font=("Segoe UI", 9, "bold"), anchor="w"
             ).grid(row=0, column=0, sticky="w", padx=5, pady=2)

    app.search_input = tk.Entry(bot_frame, bg=P(app, "bg_input"),
                                fg=P(app, "fg_accent"),
                                insertbackground=P(app, "fg_text"), bd=1,
                                font=("Consolas", 10))
    app.search_input.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    app.search_input.bind("<KeyRelease>", lambda e: _on_filter_change(app))
    app.search_input.bind("<Return>",       lambda e: app.search_next())
    app.search_input.bind("<Shift-Return>", lambda e: app.search_prev())
    app.search_input.bind("<Escape>",       lambda e: app.search_clear())

    nav = tk.Frame(bot_frame, bg=P(app, "bg_panel"))
    nav.grid(row=0, column=2, sticky="e", padx=5)

    app.search_prev_btn = _btn(nav, "◀", P(app, "idle"),
                               padx=6, pady=0, command=app.search_prev)
    app.search_prev_btn.pack(side=tk.LEFT, padx=1)

    app.search_next_btn = _btn(nav, "▶", P(app, "idle"),
                               padx=6, pady=0, command=app.search_next)
    app.search_next_btn.pack(side=tk.LEFT, padx=1)

    app.search_counter = tk.Label(nav, text="0 / 0",
                                  bg=P(app, "bg_panel"), fg=P(app, "fg_muted"),
                                  font=("Consolas", 9))
    app.search_counter.pack(side=tk.LEFT, padx=(6, 0))

    tk.Label(bot_frame, text=Localization.get("cmd_lbl"),
             background=P(app, "bg_panel"), foreground=P(app, "fg_text"),
             font=("Segoe UI", 9, "bold"), anchor="w"
             ).grid(row=1, column=0, sticky="w", padx=5, pady=2)

    app.cmd_input = tk.Entry(bot_frame, bg=P(app, "bg_widget"),
                             fg=P(app, "fg_text"),
                             insertbackground=P(app, "fg_text"), bd=1,
                             font=("Consolas", 10))
    app.cmd_input.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
    app.cmd_input.bind("<Return>", lambda e: app.send_cmd())
    app.cmd_input.bind("<Up>",     lambda e: _history_prev(app))
    app.cmd_input.bind("<Down>",   lambda e: _history_next(app))

    app.send_btn = _btn(bot_frame, Localization.get("send_btn"),
                        P(app, "primary"), padx=12, pady=2,
                        command=app.send_cmd)
    app.send_btn.grid(row=1, column=2, sticky="ew", padx=5, pady=2)


def _on_filter_change(app):
    from monitor_logic import MonitorLogic
    MonitorLogic.update_filter(app)


def _history_prev(app):
    from monitor_logic import MonitorLogic
    MonitorLogic.history_prev(app)


def _history_next(app):
    from monitor_logic import MonitorLogic
    MonitorLogic.history_next(app)


# ─────────────────────── LOG ───────────────────────

def _build_log_area(app):
    from tkinter import font as tkfont
    if not hasattr(app, "log_font"):
        app.log_font = tkfont.Font(family="Consolas",
                                   size=getattr(app, "log_font_size", 10))

    app.log_text = tk.Text(app.root, bg=P(app, "bg_log"), fg=P(app, "fg_text"),
                           insertbackground=P(app, "fg_text"),
                           selectbackground=P(app, "bg_select"),
                           font=app.log_font, state=tk.NORMAL)
    app.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5, pady=5)

    app.log_text.tag_config("normal", foreground=P(app, "fg_text"))
    app.log_text.tag_config("search_match",
                            background=P(app, "search_match"),
                            foreground=P(app, "search_fg"))
    app.log_text.tag_config("search_active",
                            background=P(app, "search_active"),
                            foreground=P(app, "search_fg"))

    app.scrollbar = ttk.Scrollbar(app.root, command=app.log_text.yview)
    app.scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
    app.log_text.config(yscrollcommand=app.scrollbar.set)


def apply_log_font(app):
    if not hasattr(app, "log_font"):
        return
    try:
        app.log_font.configure(size=getattr(app, "log_font_size", 10))
    except Exception:
        pass


# ─────────────────────── ОБНОВЛЕНИЕ ЭЛЕМЕНТОВ ───────────────────────

def refresh_macro_buttons(app):
    default_prefix = Localization.get("macro_default")
    for i, (name_e, cmd_e) in enumerate(app.macro_entries):
        name = name_e.get().strip()
        app.macro_buttons[i].config(text=name if name else f"{default_prefix} {i+1}")


def set_scroll_state(app):
    if app.freeze_scroll:
        set_button_colors(app.scroll_btn, P(app, "warn"))
        app.scroll_btn.config(text=Localization.get("unfreeze_screen"))
    else:
        set_button_colors(app.scroll_btn, P(app, "idle"))
        app.scroll_btn.config(text=Localization.get("freeze_screen"))


def set_time_state(app):
    if app.show_time:
        set_button_colors(app.time_btn, P(app, "success"))
        app.time_btn.config(text=Localization.get("time_on"))
    else:
        set_button_colors(app.time_btn, P(app, "idle"))
        app.time_btn.config(text=Localization.get("time_off"))


def set_delta_state(app):
    if app.show_delta:
        set_button_colors(app.delta_btn, P(app, "success"))
        app.delta_btn.config(text=Localization.get("delta_on"))
    else:
        set_button_colors(app.delta_btn, P(app, "idle"))
        app.delta_btn.config(text=Localization.get("delta_off"))


def update_connection_indicator(app, connected):
    if connected:
        app.conn_indicator.itemconfig(app.conn_indicator_circle,
                                      fill=P(app, "ind_green"))
        app.conn_indicator_label.config(
            text=Localization.get("conn_state_connected", "Online"),
            fg=P(app, "ind_green"))
    else:
        app.conn_indicator.itemconfig(app.conn_indicator_circle,
                                      fill=P(app, "ind_grey"))
        app.conn_indicator_label.config(
            text=Localization.get("conn_state_disconnected", "Offline"),
            fg=P(app, "fg_disabled"))


def update_autoconnect_indicator(app):
    if app.auto_conn_var.get():
        app.auto_conn_chk.config(fg=P(app, "ind_blue"))
    else:
        app.auto_conn_chk.config(fg=P(app, "fg_text"))


def update_line_counter(app):
    if not hasattr(app, "line_counter_label"):
        return
    total = len(app.all_lines)
    visible = sum(1 for t, l, _ in app.all_lines
                  if _visible_quick(app, t, l))
    limit = app.max_lines_var.get()
    app.line_counter_label.config(
        text=f"Lines: {visible} / {total}  (max {limit})")


def _visible_quick(app, msg_type, line_text):
    if msg_type == "RX" and not app.show_rx.get():
        return False
    if msg_type == "TX" and not app.show_tx.get():
        return False
    if app.filter_keyword and app.filter_keyword not in line_text.lower():
        return False
    return True


def update_search_counter(app, current=0, total=0):
    if hasattr(app, "search_counter"):
        app.search_counter.config(text=f"{current} / {total}")


# ─────────────────────── МИГАНИЕ ───────────────────────

def flash_widget(widget, times=1, on_color="#ffffff", interval=100):
    if not widget.winfo_exists():
        return

    def restore():
        if not widget.winfo_exists():
            return
        bg = widget._hover_bg if getattr(widget, "_hovered", False) else widget._normal_bg
        widget.config(bg=bg)

    def _off(n):
        if not widget.winfo_exists():
            return
        restore()
        if n > 1:
            widget.after(interval, lambda: _on(n - 1))

    def _on(n):
        if not widget.winfo_exists():
            return
        widget.config(bg=on_color)
        widget.after(interval, lambda: _off(n))

    _on(times)


def flash_rx_indicator(app):
    if not app.rx_chk.winfo_exists():
        return
    accent = P(app, "fg_accent")
    app.rx_chk.config(fg="#7cff9b")
    app.root.after(150, lambda: app.rx_chk.winfo_exists()
                   and app.rx_chk.config(fg=accent))