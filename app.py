"""
Application class. Glues UI (layouts), logic (monitor_logic),
config (monitor_config) and backend (serial_core).
"""

import os
import sys
import tkinter as tk

from serial_core import SerialCore
from monitor_config import MonitorConfig, Localization
from monitor_logic import MonitorLogic
from theme import get_palette
import layouts
import layouts_settings
from shortcuts import install_keyboard_shortcuts


APP_TITLE = "SerialB"


def _app_dir():
    """Folder with the executable (or script)."""
    if getattr(sys, "frozen", False):
        p = os.path.dirname(sys.executable)
        if sys.platform == "darwin" and ".app/Contents/MacOS" in p:
            p = os.path.abspath(os.path.join(p, "..", "..", ".."))
        return p
    return os.path.dirname(os.path.abspath(__file__))


def _bundled_dir():
    """PyInstaller temp unpack folder (for embedded resources)."""
    return getattr(sys, "_MEIPASS", None)


def _find_resource(filename):
    """
    Search order:
      1. Inside the bundled exe (_MEIPASS).
      2. Next to the exe (or script).
    Returns absolute path or None.
    """
    candidates = []
    bundled = _bundled_dir()
    if bundled:
        candidates.append(os.path.join(bundled, filename))
    candidates.append(os.path.join(_app_dir(), filename))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), filename))
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None


class SerialMonitorApp:
    def __init__(self, root):
        self.root = root

        # ── Fit window to screen ──
        screen_w = root.winfo_screenwidth()
        screen_h = root.winfo_screenheight()

        want_w, want_h = 1450, 700
        win_w = min(want_w, int(screen_w * 0.92))
        win_h = min(want_h, int(screen_h * 0.92))

        min_w, min_h = 900, 560
        win_w = max(win_w, min_w)
        win_h = max(win_h, min_h)

        pos_x = max(0, (screen_w - win_w) // 2)
        pos_y = max(0, (screen_h - win_h) // 3)

        root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        root.minsize(min_w, min_h)

        # ── Backend BEFORE load_config ──
        self.backend = SerialCore(self.process_new_line, self.append_system_msg)

        self.theme_name = "system"
        self.palette = get_palette(self.theme_name)
        self.log_font_size = 10

        Localization.load_languages()
        MonitorConfig.load_config(self)

        self.root.configure(bg=self.palette["bg_root"])

        # ── Hard-coded window title ──
        self.root.title(APP_TITLE)

        # ── Window + tray icon ──
        self._install_icon()

        layouts.set_theme_mode(self.palette.get("is_dark", True))

        self.freeze_scroll = False
        self.show_time = True
        self.show_delta = False
        self.show_rx = tk.BooleanVar(value=True)
        self.show_tx = tk.BooleanVar(value=True)
        self.last_line_time = None

        self.all_lines = []
        self.filter_keyword = ""
        self.macro_buttons = []
        self.macro_entries = []
        self.max_lines_var = tk.IntVar(value=5000)

        self.triggers_data = [
            {"active": True, "text": "exception"},
            {"active": True, "text": "guru meditation error"},
        ]
        self.highlight_data = [
            {"active": True, "text": "ERROR", "match": "part", "mode": "line", "fg": "#f44747", "bg": ""},
            {"active": True, "text": "WARNING", "match": "part", "mode": "line", "fg": "#cca700", "bg": ""},
        ]
        self.ranges_data = [
            {"active": True, "min": "2", "max": "4", "mode": "word", "fg": "#4ec9b0", "bg": ""},
        ]
        self.deltas_data = [
            {"active": True, "min": "100", "max": "1000", "fg": "#cca700"},
        ]

        self.cmd_history = []
        self.history_index = -1

        self._search_hits = []
        self._search_idx = -1

        layouts.build_main_ui(self)
        MonitorConfig.setup_context_menu(self)
        self.refresh_ports()
        MonitorConfig.load_config(self)

        self._bind_reactive_updates()
        install_keyboard_shortcuts(self.root)
        self._bind_font_shortcuts()

        # повторно через 200 мс — добить иконку после полной отрисовки
        self.root.after(200, self._install_icon)

    # ---------- Icon ----------

    def _install_icon(self):
        """
        Ставит иконку окна/трея.
        На Windows — через WinAPI (надёжно, Tk не перетрёт).
        На Linux/macOS — через iconphoto (.png).
        Вызывается несколько раз с задержкой, чтобы победить
        позднюю внутреннюю инициализацию Tkinter.
        """
        def _apply_tk():
            try:
                ico = _find_resource("serialb.ico")
                png = _find_resource("serialb.png")

                if sys.platform.startswith("win"):
                    if ico:
                        try:
                            self.root.iconbitmap(default=ico)
                        except Exception:
                            pass
                        try:
                            self.root.iconbitmap(ico)
                        except Exception:
                            pass
                else:
                    if png:
                        self._icon_img = tk.PhotoImage(file=png)
                        self.root.iconphoto(True, self._icon_img)
            except Exception:
                pass

        def _apply_winapi():
            """Прямой вызов WinAPI — гарантированный результат на Windows."""
            if not sys.platform.startswith("win"):
                return
            ico = _find_resource("serialb.ico")
            if not ico:
                return
            try:
                import ctypes
                from ctypes import wintypes

                user32 = ctypes.windll.user32

                IMAGE_ICON       = 1
                LR_LOADFROMFILE  = 0x00000010
                WM_SETICON       = 0x0080
                ICON_SMALL       = 0
                ICON_BIG         = 1

                hwnd = int(self.root.winfo_id())
                # Tk-окно — дочернее; настоящее окно верхнего уровня:
                GetParent = user32.GetParent
                root_hwnd = GetParent(hwnd) or hwnd

                # 16×16 — для трея и заголовка окна
                hicon_small = user32.LoadImageW(
                    None, ico, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)
                if hicon_small:
                    user32.SendMessageW(root_hwnd, WM_SETICON,
                                        ICON_SMALL, hicon_small)

                # 32×32 — для панели задач и Alt+Tab
                hicon_big = user32.LoadImageW(
                    None, ico, IMAGE_ICON, 32, 32, LR_LOADFROMFILE)
                if hicon_big:
                    user32.SendMessageW(root_hwnd, WM_SETICON,
                                        ICON_BIG, hicon_big)
            except Exception:
                pass

        def _apply_all():
            _apply_tk()
            _apply_winapi()

        # сразу
        _apply_all()
        # повторы — на случай поздней перезаписи Tk
        self.root.after(50,  _apply_all)
        self.root.after(200, _apply_all)
        self.root.after(500, _apply_all)
        self.root.after(1500, _apply_all)

    # ---------- Reactivity ----------

    def _bind_reactive_updates(self):
        self.show_rx.trace_add("write", lambda *_: self.refresh_view_buttons())
        self.show_tx.trace_add("write", lambda *_: self.refresh_view_buttons())
        self.max_lines_var.trace_add("write", lambda *_: self.update_max_lines_label())

    def refresh_view_buttons(self):
        layouts.update_line_counter(self)

    def update_max_lines_label(self):
        layouts.update_line_counter(self)

    # ---------- Font hotkeys ----------

    def _bind_font_shortcuts(self):
        for seq in ("<Control-equal>", "<Control-plus>", "<Control-KP_Add>"):
            self.root.bind_all(seq, lambda e: (self.log_font_inc(), "break")[1])
        for seq in ("<Control-minus>", "<Control-KP_Subtract>"):
            self.root.bind_all(seq, lambda e: (self.log_font_dec(), "break")[1])
        for seq in ("<Control-Key-0>", "<Control-KP_0>"):
            self.root.bind_all(seq, lambda e: (self.log_font_reset(), "break")[1])

        self.root.bind_all("<Control-MouseWheel>", self._on_ctrl_wheel)
        self.root.bind_all("<Control-Button-4>",   self._on_ctrl_wheel_linux)
        self.root.bind_all("<Control-Button-5>",   self._on_ctrl_wheel_linux)

    def _on_ctrl_wheel(self, event):
        if event.delta > 0:
            self.log_font_inc()
        elif event.delta < 0:
            self.log_font_dec()
        return "break"

    def _on_ctrl_wheel_linux(self, event):
        if event.num == 4:
            self.log_font_inc()
        elif event.num == 5:
            self.log_font_dec()
        return "break"

    # ---------- Log font ----------

    def set_log_font_size(self, size, save=True):
        try:
            size = int(size)
        except (TypeError, ValueError):
            return
        size = max(6, min(48, size))
        self.log_font_size = size
        layouts.apply_log_font(self)
        if save:
            MonitorConfig.save_config(self)

    def log_font_inc(self):
        self.set_log_font_size(self.log_font_size + 1)

    def log_font_dec(self):
        self.set_log_font_size(self.log_font_size - 1)

    def log_font_reset(self):
        self.set_log_font_size(10)

    # ---------- Handlers ----------

    def refresh_ports(self):
        ports = self.backend.get_ports()
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)

    def on_scale_move(self, val):
        MonitorLogic.on_scale_move(self, val)

    def on_entry_type(self):
        MonitorLogic.on_entry_type(self)

    def on_autoconnect_toggle(self):
        layouts.update_autoconnect_indicator(self)

    def press_connect(self):
        import tkinter.messagebox as messagebox
        try:
            int(self.baud_combo.get())
        except ValueError:
            messagebox.showerror(Localization.get("dlg_err"),
                                 Localization.get("msg_baud_not_number"))
            return
        MonitorLogic.press_connect(self)

    def press_disconnect(self):
        MonitorLogic.press_disconnect(self)

    def send_cmd(self):
        MonitorLogic.send_cmd(self)

    def process_new_line(self, text):
        MonitorLogic.process_line_with_type(self, "RX", f"[RX] {text}")
        layouts.flash_rx_indicator(self)
        layouts.update_line_counter(self)
        from monitor_logic import SearchController
        SearchController.refresh(self)

    def append_system_msg(self, tag, msg):
        MonitorLogic.append_system_msg(self, tag, msg)
        layouts.update_line_counter(self)

    def rebuild_log_view(self):
        MonitorLogic.rebuild_log_view(self)
        MonitorConfig.save_config(self)

    def clear_log(self):
        self.log_text.delete("1.0", tk.END)
        self.all_lines.clear()
        self.last_line_time = None
        layouts.update_line_counter(self)
        layouts.update_search_counter(self, 0, 0)
        self._search_hits = []
        self._search_idx = -1

    def toggle_scroll(self):
        self.freeze_scroll = not self.freeze_scroll
        layouts.set_scroll_state(self)
        MonitorConfig.save_config(self)

    def toggle_time(self):
        self.show_time = not self.show_time
        layouts.set_time_state(self)
        MonitorConfig.save_config(self)

    def toggle_delta(self):
        self.show_delta = not self.show_delta
        layouts.set_delta_state(self)
        MonitorConfig.save_config(self)

    def copy_clipboard(self):
        MonitorLogic.copy_clipboard(self)

    def run_macro(self, idx):
        import tkinter.messagebox as messagebox
        cmd = self.macro_entries[idx][1].get().strip()
        if cmd:
            MonitorLogic.send_specific_cmd(self, cmd)
        else:
            messagebox.showwarning(
                Localization.get("dlg_macro"),
                Localization.get("msg_macro_not_set").format(n=idx + 1),
            )

    def update_macro_buttons(self):
        layouts.refresh_macro_buttons(self)

    def open_settings_window(self):
        layouts_settings.open_settings_window(self)

    def open_settings_on_general(self):
        layouts_settings.open_settings_window(self, initial_tab="general")

    # ---------- External links ----------

    def open_coffee_link(self):
        import webbrowser
        webbrowser.open("https://buymeacoffee.com/borisovith")

    def open_github_link(self):
        import webbrowser
        webbrowser.open("https://github.com/Borisovith/SerialB")

    def open_manual(self):
        """
        Открывает мануал в браузере.
        Язык RU → русская версия, иначе английская.
        Ищет файл сначала в exe (вшитый), потом рядом с exe.
        """
        import webbrowser

        if Localization.current_lang == "ru":
            filename = "SerialB_Manual_RU.html"
        else:
            filename = "SerialB_Manual_EN.html"

        path = _find_resource(filename)
        if path:
            webbrowser.open("file://" + os.path.abspath(path))
        else:
            webbrowser.open("https://github.com/Borisovith/SerialB")

    # ---------- Search ----------

    def search_next(self):
        from monitor_logic import SearchController
        SearchController.next(self)

    def search_prev(self):
        from monitor_logic import SearchController
        SearchController.prev(self)

    def search_clear(self):
        from monitor_logic import SearchController
        SearchController.clear(self)

    # ---------- Theme ----------

    def on_theme_change(self, name):
        self.theme_name = name
        self.palette = get_palette(name)
        layouts.set_theme_mode(self.palette.get("is_dark", True))

        for w in self.root.winfo_children():
            w.destroy()

        self.macro_buttons.clear()
        self.macro_entries.clear()

        layouts.build_main_ui(self)
        MonitorConfig.setup_context_menu(self)
        self.refresh_ports()

        layouts.set_scroll_state(self)
        layouts.set_time_state(self)
        layouts.set_delta_state(self)
        layouts.update_connection_indicator(self, self.backend.running)
        layouts.update_autoconnect_indicator(self)
        layouts.update_line_counter(self)
        layouts.apply_log_font(self)

        self.root.configure(bg=self.palette["bg_root"])
        self.root.title(APP_TITLE)
        self._install_icon()   # переустановить иконку после пересборки UI

        self.rebuild_log_view()

        MonitorConfig.save_config(self)