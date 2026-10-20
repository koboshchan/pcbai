"""Exclusive USB serial session; firmware executes in RAM, never replaces main.py."""
import glob
import json
import subprocess
import time
from pathlib import Path
import serial


class Pico:
    def __init__(self, port=None):
        ports = [port] if port else glob.glob("/dev/cu.usbmodem*")
        if len(ports) != 1:
            raise RuntimeError("Expected exactly one Pico USB serial device")
        self.port = ports[0]
        self.serial = None

    def until(self, marker, timeout=8):
        end = time.monotonic() + timeout
        data = bytearray()
        while time.monotonic() < end:
            data.extend(self.serial.read(1024))
            if marker in data:
                return bytes(data)
            if len(data) > 200000:
                raise RuntimeError("Serial response exceeds bound")
        raise TimeoutError("Serial stage timed out: " + repr(data[-1000:]))

    def __enter__(self):
        owners = subprocess.run(["lsof", self.port], capture_output=True, text=True)
        if owners.stdout.strip():
            raise RuntimeError("Serial port is already owned")
        self.serial = serial.Serial(self.port, 115200, timeout=.1,
                                    write_timeout=5, exclusive=True)
        try:
            self.serial.write(b"\r\x03\x03")
            time.sleep(.3)
            self.serial.reset_input_buffer()
            self.serial.write(b"\x01")
            self.until(b"raw REPL")
            root = Path(__file__).resolve().parent
            encoding = (root / "encoding.py").read_text()
            firmware = (root / "firmware.py").read_text()
            # Concatenate trusted source in RAM; MicroPython has no types module.
            firmware = firmware.replace(
                "from encoding import words, validate_pixels, score_voltage", "")
            code = encoding + "\n" + firmware + "\nmain()\n"
            for i in range(0, len(code), 128):
                self.serial.write(code[i:i+128].encode())
                time.sleep(.005)
            self.serial.write(b"\x04")
            self.until(b'"protocol": 1}')
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def call(self, request):
        payload = json.dumps(request, separators=(",", ":")).encode() + b"\n"
        if len(payload) > 4096:
            raise ValueError("Request too long")
        self.serial.write(payload)
        end = time.monotonic() + 15
        while time.monotonic() < end:
            line = self.serial.readline(200000)
            if not line.strip():
                continue
            reply = json.loads(line)
            if "error" in reply:
                raise RuntimeError(json.dumps(reply, separators=(",", ":")))
            return reply
        raise TimeoutError("No Pico reply")

    def __exit__(self, *args):
        if self.serial is None:
            return
        try:
            self.call({"op": "quit"})
        except Exception:
            pass
        finally:
            # Interrupt runs firmware finally to disable outputs before REPL.
            self.serial.write(b"\x03\x03\x02")
            self.serial.close()
            self.serial = None
