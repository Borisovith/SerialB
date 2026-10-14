import os
import sys
import shutil
import json
import tkinter as tk
from tkinter import filedialog

from theme import get_palette


APP_NAME = "SerialB"
DEFAULT_LANG = "en"


def _is_frozen():
    return getattr(sys, "frozen", False)


def _exe_dir():
    """Folder with the executable (or script)."""
    if _is_frozen():
        p = os.path.dirname(sys.executable)
        # macOS .app: .../SerialB.app/Contents/MacOS/SerialB
        if sys.platform == "darwin" and ".app/Contents/MacOS" in p:
            p = os.path.abspath(os.path.join(p, "..", "..", ".."))
        return p
    return os.path.dirname(os.path.abspath(__file__))


def _bundled_dir():
    """PyInstaller temp unpack folder (for embedded resources)."""
    return getattr(sys, "_MEIPASS", None)


# Config always next to the exe
CONFIG_FILE = os.path.join(_exe_dir(), "config.json")


def _lang_search_dirs():
    """
    lang/ search order:
    1. Next to the exe — priority.
    2. Inside the exe (_MEIPASS) — embedded languages.
    3. Next to the script (when running from sources).
    """
    dirs = [os.path.join(_exe_dir(), "lang")]
    bundled = _bundled_dir()
    if bundled:
        dirs.append(os.path.join(bundled, "lang"))
    dirs.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lang"))
    return dirs


def ensure_lang_dir():
    """
    On the first launch of the exe: if there is no lang/ folder
    next to the exe, unpack ONLY en.json there — as an example
    for editing and as the fallback language.
    """
    if not _is_frozen():
        return

    exe_lang = os.path.join(_exe_dir(), "lang")
    if os.path.isdir(exe_lang):
        return

    bundled = _bundled_dir()
    if not bundled:
        return

    bundled_lang = os.path.join(bundled, "lang")
    if not os.path.isdir(bundled_lang):
        return

    src = os.path.join(bundled_lang, "en.json")
    if not os.path.exists(src):
        return

    try:
        os.makedirs(exe_lang, exist_ok=True)
        shutil.copy2(src, os.path.join(exe_lang, "en.json"))
    except Exception:
        pass


class Localization:
    current_lang = DEFAULT_LANG
    translations = {}
    available_langs = {}

    @classmethod
    def load_languages(cls):
        ensure_lang_dir()

        cls.available_langs = {}
        seen = set()
        for lang_dir in _lang_search_dirs():
            if not os.path.isdir(lang_dir):
                continue
            for filename in sorted(os.listdir(lang_dir)):
                if not filename.endswith(".json"):
                    continue
                code = filename[:-5]
                if code in seen:
                    continue
                path = os.path.join(lang_dir, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    name = data.get("lang_name", code)
                    cls.available_langs[code] = {"name": name, "data": data}
                    seen.add(code)
                except Exception:
                    continue

        if cls.current_lang not in cls.available_langs and cls.available_langs:
            if DEFAULT_LANG in cls.available_langs:
                cls.current_lang = DEFAULT_LANG
            else:
                cls.current_lang = list(cls.available_langs.keys())[0]

        cls.translations = cls.available_langs.get(cls.current_lang, {}).get("data", {})

    @classmethod
    def set_language(cls, code):
        if code in cls.available_langs:
            cls.current_lang = code
            cls.translations = cls.available_langs[code]["data"]

    @classmethod
    def get(cls, key, default=""):
        return cls.translations.get(key, default)


class MonitorConfig:

    @staticmethod
    def save_config(app):
        try:
            data = {
                "language": Localization.current_lang,
                "theme": getattr(app, "theme_name", "system"),

                "last_port": app.port_combo.get(),
                "auto_connect": 1 if app.auto_conn_var.get() else 0,
                "reset_on_connect": 1 if app.reset_var.get() else 0,
                "baudrate": app.baud_combo.get(),
                "max_lines": app.max_lines_var.get(),

                "timeout": int(getattr(app.backend, "timeout_ms", 50)),
                "log_font_size": int(getattr(app, "log_font_size", 10)),

                "freeze_scroll": 1 if app.freeze_scroll else 0,
                "show_time":     1 if app.show_time else 0,
                "show_delta":    1 if app.show_delta else 0,
                "show_rx":       1 if app.show_rx.get() else 0,
                "show_tx":       1 if app.show_tx.get() else 0,

                "triggers": app.triggers_data,
                "highlights": app.highlight_data,
                "ranges": app.ranges_data,
                "deltas": app.deltas_data,
                "macros": [{"name": n.get(), "cmd": c.get()} for n, c in app.macro_entries],
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    @staticmethod
    def load_config(app):
        Localization.load_languages()
        if not os.path.exists(CONFIG_FILE):
            return

        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        if "theme" in data:
            app.theme_name = data["theme"]
            app.palette = get_palette(app.theme_name)
        if "language" in data:
            Localization.set_language(data["language"])

        if "log_font_size" in data:
            try:
                app.log_font_size = max(6, min(48, int(data["log_font_size"])))
            except (TypeError, ValueError):
                pass

        if "timeout" in data:
            try:
                t = int(data["timeout"])
            except (TypeError, ValueError):
                t = 50
            t = max(1, min(5000, t))
            app.backend.timeout_ms = t

        if not hasattr(app, "port_combo"):
            return

        try:
            if "baudrate" in data:
                app.baud_combo.set(data["baudrate"])
            if "max_lines" in data:
                app.max_lines_var.set(data["max_lines"])

            t = int(getattr(app.backend, "timeout_ms", 50))
            if t <= 500:
                app.timeout_scale.set(t)
            app.timeout_entry.delete(0, tk.END)
            app.timeout_entry.insert(0, str(t))

            if "reset_on_connect" in data:
                app.reset_var.set(data["reset_on_connect"] == 1)
            if "auto_connect" in data:
                app.auto_conn_var.set(data["auto_connect"] == 1)

            if "freeze_scroll" in data:
                app.freeze_scroll = bool(data["freeze_scroll"])
            if "show_time" in data:
                app.show_time = bool(data["show_time"])
            if "show_delta" in data:
                app.show_delta = bool(data["show_delta"])
            if "show_rx" in data:
                app.show_rx.set(bool(data["show_rx"]))
            if "show_tx" in data:
                app.show_tx.set(bool(data["show_tx"]))

            if "triggers" in data and isinstance(data["triggers"], list):
                app.triggers_data = data["triggers"]
            if "highlights" in data and isinstance(data["highlights"], list):
                app.highlight_data = data["highlights"]
            if "ranges" in data and isinstance(data["ranges"], list):
                app.ranges_data = data["ranges"]
            if "deltas" in data and isinstance(data["deltas"], list):
                app.deltas_data = data["deltas"]

            if "macros" in data and isinstance(data["macros"], list):
                for i, m in enumerate(data["macros"]):
                    if i < len(app.macro_entries):
                        app.macro_entries[i][0].delete(0, tk.END)
                        app.macro_entries[i][0].insert(0, m.get("name", ""))
                        app.macro_entries[i][1].delete(0, tk.END)
                        app.macro_entries[i][1].insert(0, m.get("cmd", ""))
            app.update_macro_buttons()

            if "last_port" in data and data["last_port"]:
                current_ports = app.port_combo["values"]
                if data["last_port"] in current_ports:
                    idx = current_ports.index(data["last_port"])
                    app.port_combo.current(idx)
                    if app.auto_conn_var.get():
                        app.root.after(200, app.press_connect)

            try:
                from layouts import (set_scroll_state, set_time_state,
                                     set_delta_state, apply_log_font)
                set_scroll_state(app)
                set_time_state(app)
                set_delta_state(app)
                apply_log_font(app)
            except Exception:
                pass

            try:
                from monitor_logic import MonitorLogic
                MonitorLogic.rebuild_log_view(app)
            except Exception:
                pass

        except Exception:
            pass

    @staticmethod
    def setup_context_menu(app):
        p = app.palette
        app.context_menu = tk.Menu(app.root, tearoff=0,
                                   bg=p.get("bg_menu", "#252526"),
                                   fg=p.get("fg_text", "white"),
                                   activebackground=p.get("bg_select", "#0e639c"))
        app.context_menu.add_command(
            label=Localization.get("copy_selected"),
            command=lambda: MonitorConfig.copy_selected(app))
        app.log_text.bind("<Button-3>", lambda e: MonitorConfig.show_popup(app, e))

    @staticmethod
    def show_popup(app, event):
        try:
            app.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            app.context_menu.grab_release()

    @staticmethod
    def copy_selected(app):
        try:
            selected_text = app.log_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            app.root.clipboard_clear()
            app.root.clipboard_append(selected_text)
        except tk.TclError:
            pass

    @staticmethod
    def save_file(app):
        path = filedialog.asksaveasfilename(defaultextension=".txt")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join([line[1] for line in app.all_lines]))