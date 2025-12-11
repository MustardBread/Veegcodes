import serial
import time

# Globale seriële poort
ser = None

def initialize_serial():
    """Open de seriële verbinding éénmalig bij start van het systeem."""
    global ser
    if ser is None or not ser.is_open:
        print("Opening serial port /dev/ttyUSB0...")
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
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
