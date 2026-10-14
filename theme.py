"""
Палитры и определение системной темы.
"""

import os
import sys
import subprocess


DARK = {
    "bg_root":       "#1e1e1e",
    "bg_panel":      "#252526",
    "bg_widget":     "#333333",
    "bg_input":      "#222222",
    "bg_log":        "#000000",
    "bg_listbox":    "#1e1e1e",
    "bg_menu":       "#252526",
    "bg_select":     "#0e639c",

    "fg_text":       "#d4d4d4",
    "fg_muted":      "#888888",
    "fg_disabled":   "#777777",
    "fg_accent":     "#4ec9b0",
    "fg_tx":         "#dcdcaa",
    "fg_white":      "#ffffff",
    "fg_on_idle":    "#ffffff",

    "primary":       "#0e639c",
    "primary_hl":    "#1177bb",
    "danger":        "#a1260d",
    "danger_hl":     "#c43010",
    "success":       "#2d7d46",
    "warn":          "#b8860b",
    "neutral":       "#555555",
    "neutral_hl":    "#6a6a6a",
    "idle":          "#333333",

    "ind_grey":      "#555555",
    "ind_green":     "#37c85a",
    "ind_red":       "#e14b4b",
    "ind_blue":      "#3b8eea",
    "ind_orange":    "#e08a1e",

    "search_match":  "#554400",
    "search_active": "#ffb400",
    "search_fg":     "#ffffff",

    "is_dark": True,
}

LIGHT = {
    "bg_root":       "#f3f3f3",
    "bg_panel":      "#e8e8e8",
    "bg_widget":     "#ffffff",
    "bg_input":      "#ffffff",
    "bg_log":        "#ffffff",
    "bg_listbox":    "#ffffff",
    "bg_menu":       "#f3f3f3",
    "bg_select":     "#0e639c",

    "fg_text":       "#1e1e1e",
    "fg_muted":      "#666666",
    "fg_disabled":   "#9a9a9a",
    "fg_accent":     "#007a6a",
    "fg_tx":         "#8a6d00",
    "fg_white":      "#ffffff",
    "fg_on_idle":    "#1e1e1e",

    "primary":       "#0e639c",
    "primary_hl":    "#1177bb",
    "danger":        "#c0392b",
    "danger_hl":     "#e04b3a",
    "success":       "#2d7d46",
    "warn":          "#b8860b",
    "neutral":       "#9a9a9a",
    "neutral_hl":    "#b0b0b0",
    "idle":          "#dcdcdc",

    "ind_grey":      "#9a9a9a",
    "ind_green":     "#1e9c3f",
    "ind_red":       "#d63b3b",
    "ind_blue":      "#1d6fd4",
    "ind_orange":    "#d9791a",

    "search_match":  "#fff2a8",
    "search_active": "#ffb400",
    "search_fg":     "#1e1e1e",

    "is_dark": False,
}

THEMES = {
    "dark":  DARK,
    "light": LIGHT,
}


def detect_system_theme():
    try:
        if sys.platform.startswith("win"):
            return _detect_windows()
        if sys.platform == "darwin":
            return _detect_macos()
        return _detect_linux()
    except Exception:
        return "dark"


def _detect_windows():
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if value == 1 else "dark"
    except Exception:
        return "dark"


def _detect_macos():
    try:
        out = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True, text=True, timeout=1)
        return "dark" if "Dark" in out.stdout else "light"
    except Exception:
        return "light"


def _detect_linux():
    for schema, key in (
        ("org.gnome.desktop.interface", "color-scheme"),
        ("org.gnome.desktop.interface", "gtk-theme"),
    ):
        try:
            out = subprocess.run(
                ["gsettings", "get", schema, key],
                capture_output=True, text=True, timeout=1)
            val = (out.stdout or "").lower()
            if "dark" in val or "prefer-dark" in val:
                return "dark"
            if val.strip():
                return "light"
        except Exception:
            pass

    env = os.environ.get("GTK_THEME", "").lower()
    if "dark" in env:
        return "dark"

    try:
        import configparser
        cfg_path = os.path.expanduser("~/.config/kdeglobals")
        if os.path.exists(cfg_path):
            cfg = configparser.ConfigParser()
            cfg.read(cfg_path)
            if "Colors:Window" in cfg and "BackgroundNormal" in cfg["Colors:Window"]:
                r, g, b = [int(x) for x in cfg["Colors:Window"]["BackgroundNormal"].split(",")[:3]]
                return "dark" if (r + g + b) / 3 < 128 else "light"
    except Exception:
        pass

    return "light"


def resolve_theme(name):
    if name == "system":
        return detect_system_theme()
    return name if name in THEMES else "dark"


def get_palette(name):
    return THEMES[resolve_theme(name)]