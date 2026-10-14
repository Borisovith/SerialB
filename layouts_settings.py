"""
Settings window — UI only.
Save logic is delegated to app / monitor_config.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser

from monitor_config import MonitorConfig, Localization


def _P(app, key):
    return app.palette.get(key, "#000000")


def _auto_fg(bg_hex):
    try:
        bg_hex = bg_hex.lstrip("#")
        r = int(bg_hex[0:2], 16)
        g = int(bg_hex[2:4], 16)
        b = int(bg_hex[4:6], 16)
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return "#1e1e1e" if brightness > 140 else "#ffffff"
    except Exception:
        return "#ffffff"


def _btn(parent, text, bg, fg=None, **kw):
    if fg is None:
        fg = _auto_fg(bg)
    return tk.Button(parent, text=text, bg=bg, fg=fg, bd=0, **kw)


def _style_ttk(app):
    p = app.palette
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    bg_panel = p["bg_panel"]
    bg_widget = p["bg_widget"]
    fg_text = p["fg_text"]
    fg_white = p["fg_white"]
    bg_select = p["bg_select"]
    fg_accent = p["fg_accent"]
    bg_input = p["bg_input"]

    style.configure("TNotebook", background=bg_panel, borderwidth=0)
    style.configure("TNotebook.Tab",
                    background=bg_panel, foreground=fg_text,
                    padding=(10, 5), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", bg_widget), ("active", bg_widget)],
              foreground=[("selected", fg_accent), ("active", fg_accent)])

    style.configure("TCombobox",
                    fieldbackground=bg_input, background=bg_widget,
                    foreground=fg_text, arrowcolor=fg_text, borderwidth=1)
    style.map("TCombobox",
              fieldbackground=[("readonly", bg_input)],
              foreground=[("readonly", fg_text)],
              background=[("readonly", bg_widget)])

    style.configure("TScrollbar",
                    background=bg_widget, troughcolor=bg_panel,
                    arrowcolor=fg_text, borderwidth=0)
    style.map("TScrollbar", background=[("active", bg_select)])

    style.configure("TFrame", background=bg_panel)
    style.configure("TLabel", background=bg_panel, foreground=fg_text)
    style.configure("TButton", background=bg_widget, foreground=fg_text,
                    borderwidth=0, padding=4)
    style.map("TButton",
              background=[("active", bg_select)],
              foreground=[("active", fg_white)])
    style.configure("TCheckbutton", background=bg_panel, foreground=fg_text)
    style.configure("TRadiobutton", background=bg_panel, foreground=fg_text)


def open_settings_window(app, initial_tab=None):
    _style_ttk(app)

    win = tk.Toplevel(app.root)
    win.title(Localization.get("settings_title"))
    win.geometry("900x680")
    win.configure(bg=_P(app, "bg_panel"))
    win.grab_set()

    notebook = ttk.Notebook(win)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    temp_macro_entries = _build_macros_tab(app, notebook)
    _build_triggers_tab(app, win, notebook)
    _build_highlights_tab(app, win, notebook)
    _build_ranges_tab(app, win, notebook)
    _build_deltas_tab(app, win, notebook)
    _build_general_tab(app, notebook)
    _build_about_tab(app, win, notebook)
    lang_codes, lang_combo = _build_lang_tab(app, notebook)

    tab_order = ["macros", "triggers", "highlights",
                 "ranges", "deltas", "general", "about", "lang"]
    if initial_tab in tab_order:
        notebook.select(tab_order.index(initial_tab))

    def save_all_settings():
        for i in range(6):
            app.macro_entries[i][0].delete(0, tk.END)
            app.macro_entries[i][0].insert(0, temp_macro_entries[i][0].get())
            app.macro_entries[i][1].delete(0, tk.END)
            app.macro_entries[i][1].insert(0, temp_macro_entries[i][1].get())
        app.update_macro_buttons()

        lang_changed = False
        sel_idx = lang_combo.current()
        if 0 <= sel_idx < len(lang_codes):
            chosen_code = lang_codes[sel_idx]
            if chosen_code != Localization.current_lang:
                Localization.set_language(chosen_code)
                lang_changed = True

        MonitorConfig.save_config(app)
        win.destroy()

        if lang_changed:
            messagebox.showinfo(Localization.get("dlg_info"),
                                Localization.get("msg_lang_changed"))

    _btn(win, Localization.get("save_all_btn"), _P(app, "primary"),
         padx=20, pady=8, font=("Segoe UI", 10, "bold"),
         command=save_all_settings).pack(pady=15)


# ---------------- TABS ----------------

def _build_macros_tab(app, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_macros"))

    temp_entries = []
    for i in range(6):
        curr_name = app.macro_entries[i][0].get() or f"{Localization.get('macro_default')} {i+1}"
        curr_cmd = app.macro_entries[i][1].get()

        tk.Label(tab, text=f"{Localization.get('macro_default')} {i+1}:",
                 bg=_P(app, "bg_panel"), fg=_P(app, "fg_accent"),
                 font=("Segoe UI", 9, "bold")).grid(row=i+1, column=0, sticky="w",
                                                    padx=15, pady=6)

        e_name = tk.Entry(tab, bg=_P(app, "bg_widget"), fg=_P(app, "fg_text"),
                          insertbackground=_P(app, "fg_text"),
                          bd=1, width=18, font=("Consolas", 10))
        e_name.insert(0, curr_name)
        e_name.grid(row=i+1, column=0, sticky="e", padx=(75, 0), pady=6)

        e_cmd = tk.Entry(tab, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                         insertbackground=_P(app, "fg_text"),
                         bd=1, width=50, font=("Consolas", 10))
        e_cmd.insert(0, curr_cmd)
        e_cmd.grid(row=i+1, column=1, sticky="w", padx=15, pady=6)

        temp_entries.append((e_name, e_cmd))

    return temp_entries


def _build_triggers_tab(app, parent, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_triggers"))

    frame = tk.Frame(tab, bg=_P(app, "bg_panel"))
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame, bg=_P(app, "bg_listbox"), fg=_P(app, "fg_accent"),
                         font=("Consolas", 11),
                         selectbackground=_P(app, "bg_select"), bd=1)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    def refresh():
        listbox.delete(0, tk.END)
        tpl = Localization.get("listbox_trigger")
        s_on = Localization.get("status_active_label")
        s_off = Localization.get("status_disabled_label")
        for item in app.triggers_data:
            status = s_on if item.get("active", True) else s_off
            listbox.insert(tk.END, tpl.format(status=status, text=item.get("text", "")))

    refresh()

    btns = tk.Frame(frame, bg=_P(app, "bg_panel"))
    btns.pack(side=tk.RIGHT, fill=tk.Y)

    def do_add():
        open_rule_dialog(app, parent, Localization.get("dialog_trigger"), None,
                         lambda res: (app.triggers_data.append(res), refresh()))

    def do_edit():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        open_rule_dialog(app, parent, Localization.get("dialog_trigger"),
                         app.triggers_data[idx],
                         lambda res: (app.triggers_data.__setitem__(idx, res), refresh()))

    def do_del():
        sel = listbox.curselection()
        if not sel: return
        del app.triggers_data[sel[0]]
        refresh()

    _crud_buttons(app, btns, do_add, do_edit, do_del)


def _build_highlights_tab(app, parent, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_highlights"))

    frame = tk.Frame(tab, bg=_P(app, "bg_panel"))
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame, bg=_P(app, "bg_listbox"), fg=_P(app, "fg_text"),
                         font=("Consolas", 11),
                         selectbackground=_P(app, "bg_select"), bd=1)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    def refresh():
        listbox.delete(0, tk.END)
        tpl = Localization.get("listbox_highlight")
        s_ok = Localization.get("status_ok")
        s_no = Localization.get("status_no")
        m_line = Localization.get("mode_line_name")
        m_word = Localization.get("mode_word_name")
        for item in app.highlight_data:
            status = s_ok if item.get("active", True) else s_no
            mode_str = m_line if item.get("mode", "line") == "line" else m_word
            listbox.insert(tk.END, tpl.format(
                status=status, word=item.get("text", ""),
                mode_str=mode_str, color=item.get("fg", "#ffffff")))

    refresh()

    btns = tk.Frame(frame, bg=_P(app, "bg_panel"))
    btns.pack(side=tk.RIGHT, fill=tk.Y)

    def do_add():
        open_highlight_dialog(app, parent, None,
                              lambda res: (app.highlight_data.append(res), refresh()))

    def do_edit():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        open_highlight_dialog(app, parent, app.highlight_data[idx],
                              lambda res: (app.highlight_data.__setitem__(idx, res), refresh()))

    def do_del():
        sel = listbox.curselection()
        if not sel: return
        del app.highlight_data[sel[0]]
        refresh()

    _crud_buttons(app, btns, do_add, do_edit, do_del)


def _build_ranges_tab(app, parent, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_ranges"))

    frame = tk.Frame(tab, bg=_P(app, "bg_panel"))
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame, bg=_P(app, "bg_listbox"), fg=_P(app, "fg_text"),
                         font=("Consolas", 11),
                         selectbackground=_P(app, "bg_select"), bd=1)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    def refresh():
        listbox.delete(0, tk.END)
        tpl = Localization.get("listbox_range")
        s_ok = Localization.get("status_ok")
        s_no = Localization.get("status_no")
        m_line = Localization.get("mode_line_name")
        m_word = Localization.get("mode_word_name")
        for item in app.ranges_data:
            status = s_ok if item.get("active", True) else s_no
            mode_str = m_line if item.get("mode", "line") == "line" else m_word
            listbox.insert(tk.END, tpl.format(
                status=status, min=item.get("min", "0"), max=item.get("max", "0"),
                mode_str=mode_str, color=item.get("fg", "#ffffff")))

    refresh()

    btns = tk.Frame(frame, bg=_P(app, "bg_panel"))
    btns.pack(side=tk.RIGHT, fill=tk.Y)

    def do_add():
        open_range_dialog(app, parent, None,
                          lambda res: (app.ranges_data.append(res), refresh()))

    def do_edit():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        open_range_dialog(app, parent, app.ranges_data[idx],
                          lambda res: (app.ranges_data.__setitem__(idx, res), refresh()))

    def do_del():
        sel = listbox.curselection()
        if not sel: return
        del app.ranges_data[sel[0]]
        refresh()

    _crud_buttons(app, btns, do_add, do_edit, do_del)


def _build_deltas_tab(app, parent, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_deltas"))

    frame = tk.Frame(tab, bg=_P(app, "bg_panel"))
    frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    listbox = tk.Listbox(frame, bg=_P(app, "bg_listbox"), fg=_P(app, "fg_text"),
                         font=("Consolas", 11),
                         selectbackground=_P(app, "bg_select"), bd=1)
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

    def refresh():
        listbox.delete(0, tk.END)
        tpl = Localization.get("listbox_delta")
        s_ok = Localization.get("status_ok")
        s_no = Localization.get("status_no")
        for item in app.deltas_data:
            status = s_ok if item.get("active", True) else s_no
            listbox.insert(tk.END, tpl.format(
                status=status, min=item.get("min", "0"),
                max=item.get("max", "0"), color=item.get("fg", "#cca700")))

    refresh()

    btns = tk.Frame(frame, bg=_P(app, "bg_panel"))
    btns.pack(side=tk.RIGHT, fill=tk.Y)

    def do_add():
        open_delta_dialog(app, parent, None,
                          lambda res: (app.deltas_data.append(res), refresh()))

    def do_edit():
        sel = listbox.curselection()
        if not sel: return
        idx = sel[0]
        open_delta_dialog(app, parent, app.deltas_data[idx],
                          lambda res: (app.deltas_data.__setitem__(idx, res), refresh()))

    def do_del():
        sel = listbox.curselection()
        if not sel: return
        del app.deltas_data[sel[0]]
        refresh()

    _crud_buttons(app, btns, do_add, do_edit, do_del)


def _build_general_tab(app, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_general"))

    # ── Max lines ──
    tk.Label(tab, text=Localization.get("lbl_max_lines"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
             font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(20, 5))

    entry = tk.Entry(tab, bg=_P(app, "bg_widget"), fg=_P(app, "fg_text"),
                     insertbackground=_P(app, "fg_text"),
                     bd=1, font=("Consolas", 11), width=12)
    entry.pack(anchor="w", padx=20, pady=5)
    entry.insert(0, str(app.max_lines_var.get()))

    def save_max(*_):
        try:
            val = int(entry.get().strip())
            if val >= 100:
                app.max_lines_var.set(val)
        except ValueError:
            pass

    entry.bind("<FocusOut>", save_max)
    entry.bind("<Return>", save_max)

    # ── Log font size ──
    tk.Label(tab, text=Localization.get("lbl_log_font", "Log font size:"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
             font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(25, 5))

    font_row = tk.Frame(tab, bg=_P(app, "bg_panel"))
    font_row.pack(anchor="w", padx=20, pady=5)

    font_var = tk.IntVar(value=getattr(app, "log_font_size", 10))

    def on_font_scale(val):
        size = int(float(val))
        font_var.set(size)
        app.set_log_font_size(size, save=False)

    scale = tk.Scale(font_row, from_=6, to=32, orient=tk.HORIZONTAL,
                     bg=_P(app, "bg_panel"), fg=_P(app, "fg_accent"),
                     bd=0, highlightthickness=0, width=10, length=200,
                     font=("Consolas", 8), command=on_font_scale)
    scale.set(font_var.get())
    scale.pack(side=tk.LEFT)

    font_entry = tk.Entry(font_row, bg=_P(app, "bg_widget"),
                          fg=_P(app, "fg_accent"),
                          insertbackground=_P(app, "fg_text"),
                          bd=1, font=("Consolas", 11, "bold"),
                          width=4, justify=tk.CENTER, textvariable=font_var)
    font_entry.pack(side=tk.LEFT, padx=(10, 5))

    def apply_font_entry(*_):
        try:
            size = int(font_entry.get().strip())
            if 6 <= size <= 48:
                scale.set(size)
                app.set_log_font_size(size, save=False)
        except ValueError:
            pass

    font_entry.bind("<Return>", apply_font_entry)
    font_entry.bind("<FocusOut>", apply_font_entry)

    tk.Label(font_row, text="pt",
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 9)).pack(side=tk.LEFT)

    # ── Theme ──
    tk.Label(tab, text=Localization.get("lbl_theme", "Theme:"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
             font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(25, 5))

    theme_row = tk.Frame(tab, bg=_P(app, "bg_panel"))
    theme_row.pack(anchor="w", padx=40, pady=5)

    _make_theme_choice(app, theme_row, "system",
                       Localization.get("theme_system", "System"))
    _make_theme_choice(app, theme_row, "dark",
                       Localization.get("theme_dark", "Dark"))
    _make_theme_choice(app, theme_row, "light",
                       Localization.get("theme_light", "Light"))


def _build_about_tab(app, parent, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_about", "ℹ About"))

    # ── Header ──
    tk.Label(tab, text=Localization.get("about_app_name", "SerialB"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_accent"),
             font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=30, pady=(30, 5))

    tk.Label(tab, text=Localization.get("about_version", "Version 1.0"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 9)).pack(anchor="w", padx=30, pady=(0, 20))

    tk.Label(tab,
             text=Localization.get("about_description",
                                   "Advanced serial port monitor with highlighting,\n"
                                   "triggers, macros and customizable rules."),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
             font=("Segoe UI", 10), justify="left").pack(anchor="w", padx=30, pady=(0, 25))

    # ── Buy me a coffee button ──
    coffee_btn = tk.Button(tab,
                           text=Localization.get("about_coffee_btn",
                                                 "☕  Buy me a coffee"),
                           bg="#ffdd00", fg="#000000",
                           bd=0, padx=18, pady=10, anchor="center",
                           font=("Segoe UI", 11, "bold"), cursor="hand2",
                           activebackground="#ffcc00", activeforeground="#000000",
                           command=app.open_coffee_link)
    coffee_btn._normal_bg = "#ffdd00"
    coffee_btn._hover_bg = "#ffcc00"
    coffee_btn._hovered = False
    coffee_btn.pack(anchor="w", padx=30, pady=5)

    tk.Label(tab,
             text=Localization.get("about_coffee_hint",
                                   "Support development — buymeacoffee.com/borisovith"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 8)).pack(anchor="w", padx=32, pady=(0, 20))

    # ── GitHub button ──
    github_btn = tk.Button(tab,
                           text=Localization.get("about_github_btn",
                                                 "🐙  GitHub"),
                           bg=_P(app, "idle"), fg=_P(app, "fg_on_idle"),
                           bd=0, padx=18, pady=10, anchor="center",
                           font=("Segoe UI", 11, "bold"), cursor="hand2",
                           command=app.open_github_link)
    github_btn._normal_bg = _P(app, "idle")
    github_btn._hover_bg = _P(app, "idle")
    github_btn._hovered = False
    github_btn.pack(anchor="w", padx=30, pady=5)

    tk.Label(tab,
             text=Localization.get("about_github_hint",
                                   "github.com/Borisovith/SerialB"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 8)).pack(anchor="w", padx=32, pady=(0, 20))

    # ── Documentation button ──
    doc_btn = tk.Button(tab,
                        text=Localization.get("about_doc_btn",
                                              "📖  Documentation"),
                        bg=_P(app, "idle"), fg=_P(app, "fg_on_idle"),
                        bd=0, padx=18, pady=10, anchor="center",
                        font=("Segoe UI", 11, "bold"), cursor="hand2",
                        command=app.open_manual)
    doc_btn._normal_bg = _P(app, "idle")
    doc_btn._hover_bg = _P(app, "idle")
    doc_btn._hovered = False
    doc_btn.pack(anchor="w", padx=30, pady=5)

    tk.Label(tab,
             text=Localization.get("about_doc_hint",
                                   "Opens the user manual for the current language"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 8)).pack(anchor="w", padx=32, pady=(0, 20))

    # ── Footer ──
    tk.Label(tab,
             text=Localization.get("about_made_with",
                                   "Made with ❤ for the community."),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 8, "italic")).pack(side=tk.BOTTOM, anchor="w",
                                                  padx=30, pady=15)


def _make_theme_choice(app, parent, code, label):
    bg = _P(app, "bg_panel")
    fg = _P(app, "fg_text")
    accent = _P(app, "fg_accent")
    idle = _P(app, "idle")

    current = getattr(app, "theme_name", "system")

    row = tk.Frame(parent, bg=bg, cursor="hand2")
    row.pack(anchor="w", pady=3)

    dot = tk.Canvas(row, width=16, height=16, bg=bg, highlightthickness=0)
    dot.pack(side=tk.LEFT)

    def draw(selected):
        dot.delete("all")
        dot.create_oval(2, 2, 14, 14,
                        outline=accent if selected else idle,
                        width=2,
                        fill=bg)
        if selected:
            dot.create_oval(5, 5, 11, 11, outline="", fill=accent)

    draw(current == code)

    text = tk.Label(row, text=label, bg=bg, fg=fg,
                    font=("Segoe UI", 10), cursor="hand2")
    text.pack(side=tk.LEFT, padx=(8, 0))

    def on_click(_=None):
        app.on_theme_change(code)

    for w in (row, dot, text):
        w.bind("<Button-1>", on_click)

    def on_enter(_):
        text.config(fg=accent)

    def on_leave(_):
        text.config(fg=fg)

    for w in (row, dot, text):
        w.bind("<Enter>", on_enter, add="+")
        w.bind("<Leave>", on_leave, add="+")


def _build_lang_tab(app, notebook):
    tab = tk.Frame(notebook, bg=_P(app, "bg_panel"))
    notebook.add(tab, text=Localization.get("tab_lang"))

    tk.Label(tab, text=Localization.get("lang_label"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
             font=("Segoe UI", 10)).pack(anchor="w", padx=20, pady=(20, 5))

    lang_codes = list(Localization.available_langs.keys())
    lang_names = [Localization.available_langs[c]["name"] for c in lang_codes]

    combo = ttk.Combobox(tab, values=lang_names, state="readonly",
                         width=25, font=("Segoe UI", 10))
    combo.pack(anchor="w", padx=20, pady=5)

    if Localization.current_lang in lang_codes:
        combo.current(lang_codes.index(Localization.current_lang))
    elif lang_codes:
        combo.current(0)

    tk.Label(tab, text=Localization.get("lang_restart_note"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_muted"),
             font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(0, 5))

    return lang_codes, combo


# ---------------- HELPERS ----------------

def _crud_buttons(app, parent, do_add, do_edit, do_del):
    _btn(parent, Localization.get("add_btn"), _P(app, "primary"),
         width=12, pady=4, command=do_add).pack(pady=5)
    _btn(parent, Localization.get("edit_btn"), _P(app, "idle"),
         width=12, pady=4, command=do_edit).pack(pady=5)
    _btn(parent, Localization.get("del_btn"), _P(app, "danger"),
         width=12, pady=4, command=do_del).pack(pady=5)


# ---------------- DIALOGS ----------------

def open_rule_dialog(app, parent, title_prefix, data, callback):
    dlg = tk.Toplevel(parent)
    dlg.title(Localization.get("dialog_title_prefix").format(prefix=title_prefix))
    dlg.geometry("400x220")
    dlg.configure(bg=_P(app, "bg_panel"))
    dlg.grab_set()

    active_var = tk.BooleanVar(value=data.get("active", True) if data else True)
    tk.Checkbutton(dlg, text=Localization.get("active"), variable=active_var,
                   bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=15)

    tk.Label(dlg, text=Localization.get("lbl_trigger_text"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")).pack(anchor="w", padx=20)
    ent = tk.Entry(dlg, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                   insertbackground=_P(app, "fg_text"),
                   font=("Consolas", 10), width=40)
    ent.pack(anchor="w", padx=20, pady=5)
    if data:
        ent.insert(0, data.get("text", ""))

    def save():
        text = ent.get().strip()
        if text:
            callback({"active": active_var.get(), "text": text})
            dlg.destroy()

    _btn(dlg, Localization.get("save_btn"), _P(app, "primary"),
         padx=15, pady=5, command=save).pack(pady=15)


def open_highlight_dialog(app, parent, data, callback):
    dlg = tk.Toplevel(parent)
    dlg.title(Localization.get("dialog_highlight"))
    dlg.geometry("440x420")
    dlg.configure(bg=_P(app, "bg_panel"))
    dlg.grab_set()

    active_var = tk.BooleanVar(value=data.get("active", True) if data else True)
    tk.Checkbutton(dlg, text=Localization.get("active"), variable=active_var,
                   bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=10)

    tk.Label(dlg, text=Localization.get("lbl_highlight_text"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")).pack(anchor="w", padx=20)
    ent = tk.Entry(dlg, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                   insertbackground=_P(app, "fg_text"),
                   font=("Consolas", 10), width=42)
    ent.pack(anchor="w", padx=20, pady=5)
    if data:
        ent.insert(0, data.get("text", ""))

    match_var = tk.StringVar(value=data.get("match", "part") if data else "part")
    tk.Radiobutton(dlg, text=Localization.get("lbl_match_part"), variable=match_var,
                   value="part", bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=2)
    tk.Radiobutton(dlg, text=Localization.get("lbl_match_exact"), variable=match_var,
                   value="exact", bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=2)

    tk.Label(dlg, text=Localization.get("lbl_highlight_area"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_accent"),
             font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 2))

    mode_var = tk.StringVar(value=data.get("mode", "line") if data else "line")
    tk.Radiobutton(dlg, text=Localization.get("lbl_mode_line"), variable=mode_var,
                   value="line", bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=2)
    tk.Radiobutton(dlg, text=Localization.get("lbl_mode_word"), variable=mode_var,
                   value="word", bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=2)

    fg_color = tk.StringVar(value=data.get("fg", "#f44747") if data else "#f44747")
    _color_picker(app, dlg, fg_color, Localization.get("lbl_text_color"))

    def save():
        text = ent.get().strip()
        if text:
            callback({"active": active_var.get(), "text": text,
                      "match": match_var.get(), "mode": mode_var.get(),
                      "fg": fg_color.get(), "bg": ""})
            dlg.destroy()

    _btn(dlg, Localization.get("save_btn"), _P(app, "primary"),
         padx=15, pady=5, command=save).pack(pady=10)


def open_range_dialog(app, parent, data, callback):
    dlg = tk.Toplevel(parent)
    dlg.title(Localization.get("dialog_range"))
    dlg.geometry("400x380")
    dlg.configure(bg=_P(app, "bg_panel"))
    dlg.grab_set()

    active_var = tk.BooleanVar(value=data.get("active", True) if data else True)
    tk.Checkbutton(dlg, text=Localization.get("active"), variable=active_var,
                   bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=10)

    f_inputs = tk.Frame(dlg, bg=_P(app, "bg_panel"))
    f_inputs.pack(anchor="w", padx=20, pady=5)

    tk.Label(f_inputs, text=Localization.get("lbl_range_from"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")).pack(side=tk.LEFT)
    ent_min = tk.Entry(f_inputs, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                       insertbackground=_P(app, "fg_text"),
                       font=("Consolas", 10), width=10)
    ent_min.pack(side=tk.LEFT, padx=(5, 20))
    if data:
        ent_min.insert(0, data.get("min", ""))

    tk.Label(f_inputs, text=Localization.get("lbl_range_to"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")).pack(side=tk.LEFT)
    ent_max = tk.Entry(f_inputs, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                       insertbackground=_P(app, "fg_text"),
                       font=("Consolas", 10), width=10)
    ent_max.pack(side=tk.LEFT, padx=5)
    if data:
        ent_max.insert(0, data.get("max", ""))

    tk.Label(dlg, text=Localization.get("lbl_highlight_area"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_accent"),
             font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=20, pady=(10, 2))

    mode_var = tk.StringVar(value=data.get("mode", "line") if data else "line")
    tk.Radiobutton(dlg, text=Localization.get("lbl_mode_line"), variable=mode_var,
                   value="line", bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=2)
    tk.Radiobutton(dlg, text=Localization.get("lbl_mode_word"), variable=mode_var,
                   value="word", bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=2)

    fg_color = tk.StringVar(value=data.get("fg", "#4ec9b0") if data else "#4ec9b0")
    _color_picker(app, dlg, fg_color, Localization.get("lbl_hl_color"))

    def save():
        try:
            min_v = float(ent_min.get().strip())
            max_v = float(ent_max.get().strip())
            callback({"active": active_var.get(), "min": str(min_v), "max": str(max_v),
                      "mode": mode_var.get(), "fg": fg_color.get(), "bg": ""})
            dlg.destroy()
        except ValueError:
            messagebox.showerror(Localization.get("dlg_err"),
                                 Localization.get("msg_numbers_required"))

    _btn(dlg, Localization.get("save_btn"), _P(app, "primary"),
         padx=15, pady=5, command=save).pack(pady=15)


def open_delta_dialog(app, parent, data, callback):
    dlg = tk.Toplevel(parent)
    dlg.title(Localization.get("dialog_delta"))
    dlg.geometry("400x320")
    dlg.configure(bg=_P(app, "bg_panel"))
    dlg.grab_set()

    active_var = tk.BooleanVar(value=data.get("active", True) if data else True)
    tk.Checkbutton(dlg, text=Localization.get("active"), variable=active_var,
                   bg=_P(app, "bg_panel"), fg=_P(app, "fg_text"),
                   selectcolor=_P(app, "bg_widget"),
                   activebackground=_P(app, "bg_panel"),
                   activeforeground=_P(app, "fg_accent")
                   ).pack(anchor="w", padx=20, pady=10)

    f_inputs = tk.Frame(dlg, bg=_P(app, "bg_panel"))
    f_inputs.pack(anchor="w", padx=20, pady=5)

    tk.Label(f_inputs, text=Localization.get("lbl_delta_from"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")).pack(side=tk.LEFT)
    ent_min = tk.Entry(f_inputs, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                       insertbackground=_P(app, "fg_text"),
                       font=("Consolas", 10), width=10)
    ent_min.pack(side=tk.LEFT, padx=(5, 20))
    if data:
        ent_min.insert(0, data.get("min", ""))

    tk.Label(f_inputs, text=Localization.get("lbl_delta_to"),
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")).pack(side=tk.LEFT)
    ent_max = tk.Entry(f_inputs, bg=_P(app, "bg_widget"), fg=_P(app, "fg_accent"),
                       insertbackground=_P(app, "fg_text"),
                       font=("Consolas", 10), width=10)
    ent_max.pack(side=tk.LEFT, padx=5)
    if data:
        ent_max.insert(0, data.get("max", ""))

    fg_color = tk.StringVar(value=data.get("fg", "#cca700") if data else "#cca700")
    _color_picker(app, dlg, fg_color, Localization.get("lbl_hl_color"))

    def save():
        try:
            min_v = float(ent_min.get().strip())
            max_v = float(ent_max.get().strip())
            callback({"active": active_var.get(), "min": str(min_v), "max": str(max_v),
                      "fg": fg_color.get()})
            dlg.destroy()
        except ValueError:
            messagebox.showerror(Localization.get("dlg_err"),
                                 Localization.get("msg_delta_numbers_required"))

    _btn(dlg, Localization.get("save_btn"), _P(app, "primary"),
         padx=15, pady=5, command=save).pack(pady=15)


def _color_picker(app, parent, var, label_text):
    row = tk.Frame(parent, bg=_P(app, "bg_panel"))
    row.pack(anchor="w", padx=20, pady=15)
    tk.Label(row, text=label_text,
             bg=_P(app, "bg_panel"), fg=_P(app, "fg_text")
             ).pack(side=tk.LEFT, padx=(0, 10))
    lbl = tk.Label(row, text=Localization.get("lbl_color_preview"),
                   bg=var.get(), fg="black", font=("Consolas", 9, "bold"))
    lbl.pack(side=tk.LEFT, padx=10)

    def pick():
        col = colorchooser.askcolor(initialcolor=var.get())
        if col and col[1]:
            var.set(col[1])
            lbl.config(bg=col[1])

    _btn(row, Localization.get("lbl_pick_color"), _P(app, "idle"),
         command=pick).pack(side=tk.LEFT, padx=10)