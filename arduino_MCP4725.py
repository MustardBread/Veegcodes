import serial
import time
import glob
import subprocess

# Globale seriële poort
ser = None


def _is_ch341(port: str) -> bool:
    """
    Controleer of een ttyUSB-poort een ch341-uart converter is
    """
    try:
        result = subprocess.check_output(
            ["udevadm", "info", "--query=all", "--name", port],
            text=True
        )
        return "ch341" in result.lower()
    except Exception:
        return False


def _find_ch341_port() -> str | None:
    """
    Zoek automatisch de ttyUSB-poort met ch341-uart
    """
    ports = glob.glob("/dev/ttyUSB*")

    for port in ports:
        if _is_ch341(port):
            return port

    return None


def initialize_serial():
    """Open de seriële verbinding éénmalig bij start van het systeem."""
    global ser

    if ser is not None and ser.is_open:
        return

    port = _find_ch341_port()

    if port is None:
        raise RuntimeError(
            "❌ Geen ch341-uart device gevonden! "
            "Controleer of de Arduino is aangesloten."
        )

    print(f"Opening serial port {port} (ch341)...")
    ser = serial.Serial(port, 115200, timeout=1)
    time.sleep(2)  # Arduino reset tijd
    print("Serial ready.")


def send_speed(speed):
    """Stuur de snelheid (0–100) naar de Arduino."""
    global ser

    if ser is None or not ser.is_open:
        initialize_serial()

    try:
        ser.write(f"{speed}\n".encode())
        print(f"Sent speed: {speed}")
    except Exception as e:
        print(f"Serial error while sending speed: {e}")


def close_serial():
    """Sluit de seriële verbinding netjes af."""
    global ser

    if ser is not None and ser.is_open:
        ser.close()
        print("Serial closed.")
