import tkinter as tk
from app import SerialMonitorApp


def main():
    root = tk.Tk()
    app = SerialMonitorApp(root)

    def on_closing():
        from monitor_config import MonitorConfig
        MonitorConfig.save_config(app)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()