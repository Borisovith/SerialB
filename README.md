# SerialB

**Advanced serial port monitor** with rule-based highlighting, triggers, macros, custom themes and multi-language UI.

Built with Python + Tkinter. Runs on **Windows**, **Linux** and **macOS**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](#)

---

## Features

- 🎨 **Rule-based highlighting** — keywords, numeric ranges, timing intervals
- 🛑 **Triggers** — auto-freeze the log when a stop-word appears
- ⚡ **6 programmable macros** — one-click quick commands
- 🌓 **Themes** — Dark / Light / System (Windows, macOS, Linux)
- 🔍 **Search with inline highlight** — all matches highlighted, navigate with Enter
- 🌐 **Multi-language UI** — English, Deutsch, Українська, Русский
- 📊 **Live line counter**, dynamic font size, timestamps and intervals
- 💾 **Portable** — config and languages live next to the executable
- 📦 **Single-file binaries** — no Python required to run

---

## Installation

### Option 1 — Pre-built binaries (recommended)

Grab the latest release for your platform from the [**Releases**](../../releases) page:

- `SerialB.exe` — Windows
- `SerialB` — Linux
- `SerialB.app` — macOS

Unpack, put next to it the `lang/` folder if you want external language files (optional — English is embedded), run.

### Option 2 — From source

```bash
git clone https://github.com/Borisovith/SerialB.git
cd SerialB
pip install -r requirements.txt
python main.py
```

Requirements:
- Python **3.10+** with `tkinter`
- `pyserial`

---

## Building

See **[Build.txt](Build.txt)** (English) or **[Build_RU.txt](Build_RU.txt)** (Русский) for detailed instructions.

Quick reference:

| Platform | Build on | Command | Result |
|----------|----------|---------|--------|
| Windows  | Windows  | `pyinstaller --onefile --windowed --name SerialB --icon=serialb.ico --add-data "lang;lang" main.py` | `dist\SerialB.exe` |
| Linux    | Linux    | `pyinstaller --onefile --windowed --name SerialB --add-data "lang:lang" main.py` | `dist/SerialB` |
| macOS    | macOS    | `pyinstaller --windowed --name SerialB --icon=serialb.icns --add-data "lang:lang" main.py` | `dist/SerialB.app` |

> PyInstaller is **not** a cross-compiler — build on the target OS.

---

## Usage

1. Launch **SerialB**.
2. Pick your port and baud rate, click **Connect**.
3. Open **⚙ Settings** to configure:
   - **Macros** — up to 6 quick commands
   - **Triggers** — auto-freeze on stop-words
   - **Keywords** — text highlighting rules
   - **Numeric ranges** — highlight numbers in a range
   - **Intervals** — highlight timing gaps
   - **General** — theme, font size, line limit
   - **Language** — switch UI language

### Hotkeys

| Shortcut | Action |
|----------|--------|
| `Ctrl` + `C` / `V` / `X` / `A` | Copy / Paste / Cut / Select all |
| `Ctrl` + `=` / `-` | Increase / decrease log font size |
| `Ctrl` + `0` | Reset font size |
| `Ctrl` + mouse wheel | Smooth font resize |
| `↑` / `↓` in command field | Command history |
| `Enter` / `Shift+Enter` in search | Next / previous match |
| `Esc` in search | Clear search |

---

## Project structure

```
SerialB/
├── main.py                 # entry point
├── app.py                  # application class (glues everything)
├── layouts.py              # main window — UI only
├── layouts_settings.py     # settings window — UI only
├── monitor_logic.py        # log processing / highlighting / search
├── monitor_config.py       # config save/load + localization
├── serial_core.py          # serial port I/O
├── shortcuts.py            # global hotkeys
├── theme.py                # palettes + system theme detection
├── lang/                   # language files (embedded + external)
│   ├── en.json
│   ├── de.json
│   ├── uk.json
│   └── ru.json
├── serialb.ico / .png / .icns
├── Build.txt / Build_RU.txt
├── SerialB_Manual_EN.html
└── SerialB_Manual_RU.html
```

---

## Documentation

- 🇬🇧 [User Manual (English)](SerialB_Manual_EN.html)
- 🇷🇺 [Руководство пользователя (Русский)](SerialB_Manual_RU.html)
- 🇬🇧 [Build Instructions (English)](Build.txt)
- 🇷🇺 [Инструкция по сборке (Русский)](Build_RU.txt)

---

## Configuration files

SerialB is **portable**. Everything lives next to the executable:

| File / folder | Purpose |
|---------------|---------|
| `config.json` | Your settings (port, theme, rules, macros). Created on first save. |
| `lang/`       | Language files. `en.json` is auto-unpacked on first launch. |

To reset — just delete `config.json`.

To add a custom language — copy `lang/en.json` to `lang/xx.json`, translate the values, restart.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Support

If SerialB saved you time:

<a href="https://buymeacoffee.com/borisovith">
  <img src="https://img.shields.io/badge/Buy%20me%20a%20coffee-☕-ffdd00?style=for-the-badge" alt="Buy me a coffee">
</a>

## License

[MIT](LICENSE) © 2026 Serhii