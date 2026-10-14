"""
Логика обработки логов, подсветки, триггеров, отправки команд.
Интерфейс трогает только через app.* методы.
"""

import time
import re
import tkinter as tk
from tkinter import messagebox

from monitor_config import MonitorConfig, Localization


class MonitorLogic:

    # ---------- Timeout ----------

    @staticmethod
    def on_scale_move(app, val):
        ms = int(float(val))
        app.backend.timeout_ms = ms
        app.timeout_entry.delete(0, tk.END)
        app.timeout_entry.insert(0, str(ms))

    @staticmethod
    def on_entry_type(app):
        try:
            raw_val = app.timeout_entry.get().strip()
            if len(raw_val) > 5:
                raise ValueError
            val = int(raw_val)
            if 1 <= val <= 5000:
                app.backend.timeout_ms = val
                if val <= 500:
                    app.timeout_scale.set(val)
            else:
                MonitorLogic.reset_timeout_entry(app)
        except ValueError:
            MonitorLogic.reset_timeout_entry(app)

    @staticmethod
    def reset_timeout_entry(app):
        # Возвращаемся к актуальному значению backend, а не к слайдеру,
        # чтобы случайно не потерять введённое значение из-за слайдера.
        current = int(getattr(app.backend, "timeout_ms", 50))
        app.timeout_entry.delete(0, tk.END)
        app.timeout_entry.insert(0, str(current))
        if current <= 500:
            app.timeout_scale.set(current)

    # ---------- Подключение ----------

    @staticmethod
    def press_connect(app):
        import layouts
        port = app.port_combo.get()
        if not port:
            return
        MonitorLogic.on_entry_type(app)
        if app.backend.connect(port, int(app.baud_combo.get()),
                               app.reset_var.get(), app.backend.timeout_ms):
            layouts.set_button_colors(app.conn_btn, app.palette["neutral"])
            app.conn_btn.config(state=tk.DISABLED)
            layouts.set_button_colors(app.disconn_btn, app.palette["danger"])
            app.disconn_btn.config(state=tk.NORMAL)
            app.port_combo.config(state=tk.DISABLED)
            layouts.update_connection_indicator(app, connected=True)

            app.append_system_msg(
                Localization.get("sys_tag"),
                Localization.get("msg_connected_to").format(port=port))
            MonitorConfig.save_config(app)
            app.root.after(1000, lambda: MonitorLogic.check_connection_loop(app))
        else:
            messagebox.showerror(Localization.get("dlg_err"),
                                 Localization.get("msg_port_open_fail"))

    @staticmethod
    def check_connection_loop(app):
        import layouts
        if not app.backend.running and app.conn_btn["state"] == tk.DISABLED:
            layouts.set_button_colors(app.conn_btn, app.palette["primary"])
            app.conn_btn.config(state=tk.NORMAL)
            layouts.set_button_colors(app.disconn_btn, app.palette["neutral"])
            app.disconn_btn.config(state=tk.DISABLED)
            app.port_combo.config(state="readonly")
            layouts.update_connection_indicator(app, connected=False)

        if app.auto_conn_var.get() and app.conn_btn["state"] == tk.NORMAL:
            ports = app.backend.get_ports()
            target_port = app.port_combo.get()
            if target_port in ports:
                MonitorLogic.press_connect(app)

        if hasattr(app, "root") and app.root.winfo_exists():
            app.root.after(1000, lambda: MonitorLogic.check_connection_loop(app))

    @staticmethod
    def press_disconnect(app):
        import layouts
        app.backend.disconnect()
        layouts.set_button_colors(app.conn_btn, app.palette["primary"])
        app.conn_btn.config(state=tk.NORMAL)
        layouts.set_button_colors(app.disconn_btn, app.palette["neutral"])
        app.disconn_btn.config(state=tk.DISABLED)
        app.port_combo.config(state="readonly")
        layouts.update_connection_indicator(app, connected=False)

    # ---------- Ввод команд ----------

    @staticmethod
    def send_cmd(app):
        cmd = app.cmd_input.get().strip()
        if not cmd:
            return
        if not app.cmd_history or app.cmd_history[-1] != cmd:
            app.cmd_history.append(cmd)
        app.history_index = len(app.cmd_history)
        MonitorLogic.send_specific_cmd(app, cmd)
        app.cmd_input.delete(0, tk.END)

    @staticmethod
    def history_prev(app):
        if not app.cmd_history:
            return
        if app.history_index > 0:
            app.history_index -= 1
            app.cmd_input.delete(0, tk.END)
            app.cmd_input.insert(0, app.cmd_history[app.history_index])

    @staticmethod
    def history_next(app):
        if not app.cmd_history:
            return
        if app.history_index < len(app.cmd_history) - 1:
            app.history_index += 1
            app.cmd_input.delete(0, tk.END)
            app.cmd_input.insert(0, app.cmd_history[app.history_index])
        else:
            app.history_index = len(app.cmd_history)
            app.cmd_input.delete(0, tk.END)

    @staticmethod
    def send_specific_cmd(app, cmd):
        if app.backend.ser and app.backend.ser.is_open:
            app.backend.send(cmd)
            MonitorLogic.process_line_with_type(app, "TX", f"[TX] ➔ {cmd}")
        else:
            messagebox.showwarning(Localization.get("dlg_warn"),
                                   Localization.get("msg_port_closed"))

    # ---------- Обработка строк ----------

    @staticmethod
    def process_line_with_type(app, msg_type, text):
        now = time.time()
        delta_ms = 0
        if app.last_line_time:
            delta_ms = int((now - app.last_line_time) * 1000)
        app.last_line_time = now

        prefix = ""
        if app.show_delta:
            prefix += f"[+{delta_ms}ms] "
        if app.show_time:
            prefix = f"{time.strftime('[%H:%M:%S', time.localtime(now))}.{int((now % 1)*1000):03d}] " + prefix

        full_line = f"{prefix}{text}"

        max_limit = app.max_lines_var.get()
        if len(app.all_lines) >= max_limit:
            app.all_lines.pop(0)
        app.all_lines.append((msg_type, full_line, delta_ms))

        if msg_type == "RX":
            line_lower = text.lower()
            for trig in app.triggers_data:
                if trig["active"] and trig["text"].strip():
                    if trig["text"].strip().lower() in line_lower:
                        if not app.freeze_scroll:
                            app.freeze_scroll = True
                            from layouts import set_scroll_state
                            set_scroll_state(app)
                        MonitorLogic.append_system_msg(
                            app,
                            Localization.get("trigger_tag"),
                            Localization.get("msg_trigger_fired").format(trigger=trig["text"]))
                        break

        if MonitorLogic.is_line_visible(app, msg_type, full_line):
            MonitorLogic.insert_formatted_line(app, msg_type, full_line, delta_ms)
            if not app.freeze_scroll:
                app.log_text.see(tk.END)

    @staticmethod
    def smart_word_bounds(line_text, start_pos, end_pos):
        while start_pos > 0 and line_text[start_pos - 1] not in (" ", "\t", "\n", "(", "[", "{", ";"):
            start_pos -= 1
        while end_pos < len(line_text) and line_text[end_pos] not in (" ", "\t", "\n", ")", "]", "}", ",", ";"):
            end_pos += 1
        return start_pos, end_pos

    @staticmethod
    def insert_formatted_line(app, msg_type, line_text, delta_ms=0):
        app.log_text.insert(tk.END, f"{line_text}\n", "normal")
        line_idx = app.log_text.index("end-2c linestart")

        for d_item in app.deltas_data:
            if not d_item.get("active", True):
                continue
            try:
                d_min = float(d_item["min"])
                d_max = float(d_item["max"])
                if d_min <= delta_ms <= d_max:
                    d_col = d_item["fg"]
                    d_tag = f"col_{d_col}"
                    if d_tag not in app.log_text.tag_names():
                        app.log_text.tag_config(d_tag, foreground=d_col)
                    delta_str = f"[+{delta_ms}ms]"
                    d_idx = line_text.find(delta_str)
                    if d_idx != -1:
                        app.log_text.tag_add(
                            d_tag,
                            f"{line_idx}+{d_idx}c",
                            f"{line_idx}+{d_idx + len(delta_str)}c")
            except ValueError:
                pass

        if msg_type != "RX":
            return

        payload_text = line_text
        payload_offset = 0
        rx_pos = line_text.find("[RX]")
        if rx_pos != -1:
            payload_text = line_text[rx_pos:]
            payload_offset = rx_pos

        for h in app.highlight_data:
            if not h["active"] or not h["text"].strip():
                continue
            word = h["text"].strip()
            color = h["fg"]
            tag_name = f"col_{color}"
            if tag_name not in app.log_text.tag_names():
                app.log_text.tag_config(tag_name, foreground=color)

            if h["match"] == "exact":
                pattern = r"\b" + re.escape(word) + r"\b(?![\s]*=)"
            else:
                pattern = re.escape(word)

            matches = list(re.finditer(pattern, payload_text, re.IGNORECASE))
            if matches:
                if h["mode"] == "line":
                    app.log_text.tag_add(tag_name, f"{line_idx}", f"{line_idx} lineend")
                    return
                else:
                    for m in matches:
                        start_pos = m.start() + payload_offset
                        end_pos = m.end() + payload_offset
                        s, e = MonitorLogic.smart_word_bounds(line_text, start_pos, end_pos)
                        app.log_text.tag_add(tag_name, f"{line_idx}+{s}c", f"{line_idx}+{e}c")
                    return

        ranges_matches = []
        for r in app.ranges_data:
            if not r["active"]:
                continue
            try:
                min_v = float(r["min"])
                max_v = float(r["max"])
                color = r["fg"]
                mode = r["mode"]
                for m in re.finditer(r"\b-?\d+(?:\.\d+)?\b(?!\.)", payload_text):
                    num = float(m.group(0))
                    if min_v <= num <= max_v:
                        ranges_matches.append((m, color, mode))
            except ValueError:
                continue

        if ranges_matches:
            m, color, mode = ranges_matches[0]
            tag_name = f"col_{color}"
            if tag_name not in app.log_text.tag_names():
                app.log_text.tag_config(tag_name, foreground=color)

            if mode == "line":
                app.log_text.tag_add(tag_name, f"{line_idx}", f"{line_idx} lineend")
            else:
                start_pos = m.start() + payload_offset
                end_pos = m.end() + payload_offset
                s, e = MonitorLogic.smart_word_bounds(line_text, start_pos, end_pos)
                app.log_text.tag_add(tag_name, f"{line_idx}+{s}c", f"{line_idx}+{e}c")

    @staticmethod
    def is_line_visible(app, msg_type, line_text):
        if msg_type == "RX" and not app.show_rx.get():
            return False
        if msg_type == "TX" and not app.show_tx.get():
            return False
        if app.filter_keyword and app.filter_keyword not in line_text.lower():
            return False
        return True

    @staticmethod
    def update_filter(app):
        app.filter_keyword = app.search_input.get().lower()
        MonitorLogic.rebuild_log_view(app)

    @staticmethod
    def rebuild_log_view(app):
        import layouts
        app.log_text.delete("1.0", tk.END)
        for msg_type, line, delta in app.all_lines:
            if MonitorLogic.is_line_visible(app, msg_type, line):
                MonitorLogic.insert_formatted_line(app, msg_type, line, delta)
        if not app.freeze_scroll:
            app.log_text.see(tk.END)
        layouts.update_line_counter(app)
        SearchController.refresh(app)

    @staticmethod
    def append_system_msg(app, tag, msg):
        full_msg = f"[{tag}] {msg}"
        max_limit = app.max_lines_var.get()
        if len(app.all_lines) >= max_limit:
            app.all_lines.pop(0)
        app.all_lines.append(("SYS", full_msg, 0))
        if not app.filter_keyword or app.filter_keyword in full_msg.lower():
            app.log_text.insert(tk.END, f"{full_msg}\n", "normal")
            app.log_text.see(tk.END)

    @staticmethod
    def copy_clipboard(app):
        raw_text = "\n".join([line_data[1] for line_data in app.all_lines])
        app.root.clipboard_clear()
        app.root.clipboard_append(raw_text)
        messagebox.showinfo(Localization.get("dlg_buf"), Localization.get("msg_copied"))


class SearchController:
    """Подсветка всех вхождений filter_keyword и навигация между ними."""

    @staticmethod
    def refresh(app):
        text = app.log_text
        text.tag_remove("search_match", "1.0", tk.END)
        text.tag_remove("search_active", "1.0", tk.END)

        query = app.filter_keyword.strip()
        if not query:
            app._search_hits = []
            app._search_idx = -1
            from layouts import update_search_counter
            update_search_counter(app, 0, 0)
            return

        hits = []
        start = "1.0"
        while True:
            pos = text.search(query, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(query)}c"
            text.tag_add("search_match", pos, end)
            hits.append((pos, end))
            start = end

        app._search_hits = hits
        app._search_idx = 0 if hits else -1
        SearchController._show_active(app)

    @staticmethod
    def _show_active(app):
        text = app.log_text
        text.tag_remove("search_active", "1.0", tk.END)
        hits = getattr(app, "_search_hits", [])
        idx = getattr(app, "_search_idx", -1)

        from layouts import update_search_counter
        if not hits or idx < 0:
            update_search_counter(app, 0, 0)
            return

        pos, end = hits[idx]
        text.tag_add("search_active", pos, end)
        text.see(pos)
        update_search_counter(app, idx + 1, len(hits))

    @staticmethod
    def next(app):
        hits = getattr(app, "_search_hits", [])
        if not hits:
            return
        app._search_idx = (app._search_idx + 1) % len(hits)
        SearchController._show_active(app)

    @staticmethod
    def prev(app):
        hits = getattr(app, "_search_hits", [])
        if not hits:
            return
        app._search_idx = (app._search_idx - 1) % len(hits)
        SearchController._show_active(app)

    @staticmethod
    def clear(app):
        app.search_input.delete(0, tk.END)
        MonitorLogic.update_filter(app)