import time
import threading
import serial
import serial.tools.list_ports

from monitor_config import Localization


class SerialCore:
    def __init__(self, on_line_received, on_system_msg):
        self.ser = None
        self.running = False
        self.on_line_received = on_line_received
        self.on_system_msg = on_system_msg
        self.timeout_ms = 50

    def get_ports(self):
        return [f"{p.device}" for p in serial.tools.list_ports.comports()]

    def connect(self, port, baud, reset_on_connect, timeout_ms):
        if not port:
            return False
        try:
            self.timeout_ms = timeout_ms
            self.ser = serial.Serial()
            self.ser.port = port
            self.ser.baudrate = baud
            self.ser.timeout = self.timeout_ms / 1000.0

            if not reset_on_connect:
                self.ser.dtr = False
                self.ser.rts = False

            self.ser.open()

            if reset_on_connect:
                self.ser.setDTR(False)
                self.ser.setRTS(False)
            else:
                self.ser.setDTR(False)
                self.ser.setRTS(False)
                self.ser.dtr = False
                self.ser.rts = False

            self.running = True
            threading.Thread(target=self._read_thread, daemon=True).start()
            return True
        except Exception as e:
            self.on_system_msg(Localization.get("error_tag", "Error"), str(e))
            return False

    def disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.on_system_msg(Localization.get("sys_tag", "System"),
                           Localization.get("msg_port_closed_status", "Port closed."))

    def _read_thread(self):
        buffer = b""
        while self.running:
            try:
                if self.ser:
                    self.ser.timeout = self.timeout_ms / 1000.0

                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    buffer += data
                    if b"\n" in buffer:
                        lines = buffer.split(b"\n")
                        buffer = lines.pop()
                        for line in lines:
                            text = line.decode("utf-8", errors="ignore").replace("\r", "").strip()
                            if text:
                                self.on_line_received(text)
            except Exception:
                break
            time.sleep(0.005)

    def send(self, cmd):
        if cmd and self.ser and self.ser.is_open:
            self.ser.write((cmd + "\r\n").encode("utf-8"))

    def reset_esp(self):
        if self.ser and self.ser.is_open:
            self.on_system_msg(Localization.get("action_tag", "Action"),
                               Localization.get("msg_reset_esp", "Resetting ESP32..."))
            self.ser.setDTR(False)
            self.ser.setRTS(True)
            time.sleep(0.1)
            self.ser.setRTS(False)
            self.ser.setDTR(False)
            time.sleep(0.1)
            self.ser.dtr = False
            self.ser.rts = False
        else:
            self.on_system_msg(Localization.get("warning_tag", "Warning"),
                               Localization.get("msg_port_not_connected", "Port is not connected!"))