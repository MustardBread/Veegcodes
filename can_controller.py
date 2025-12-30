import subprocess
import time
import atexit
import threading
import signal
import sys

# ============================
# CONFIG
# ============================
CAN_IFACE = "can0"
BITRATE = 250000
ERROR_CAN_ID = "07000001"

_running = True
error_active = False
last_errors = []
# ==============================
# GLOBALS
# ==============================
_error_thread_running = True
_error_thread = None

# ==============================
# CAN SEND
# ==============================
def send_command(command):
    """Verstuur een CAN-commando via de terminal."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print(f"Command sent: {command}")
    else:
        print(f"Error sending command: {result.stderr}")

def start_can_interface():
    """Start de CAN-interface."""
    command = "sudo ip link set can0 up type can bitrate 250000 sjw 4 restart-ms 100 berr-reporting on"
    send_command(command)
    time.sleep(1)

def stop_can_interface():
    """Stop de CAN-interface."""
    send_command("sudo ip link set can0 down")

# ==============================
# VALUE ENCODING
# ==============================
def decimal_to_hex(data):
    """Zet decimale waarde om naar hex in juiste formaat."""
    if data < 0:
        return format(65536 + data, '04X')
    if data > 32767:
        return format(data & 0xFFFF, '04X')
    return format(data, '04X')

def send_value(dec_value):
    """Verstuur een decimale waarde als CAN-bericht."""
    hex_value = decimal_to_hex(dec_value)
    base_command = "cansend can0 06000001#23.02.20.01"

    if 0 <= dec_value <= 32767:
        full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.00.00"
    else:
        full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.FF.FF"

    send_command(full_command)

# ==============================
# MODE CONTROL
# ==============================
def enable_absolute_position_mode():
    send_command("cansend can0 06000001#23.0D.20.01.00.00.00.00")

def disable_absolute_position_mode():
    send_command("cansend can0 06000001#23.0C.20.01.00.00.00.00")

# ============================
# ERROR DECODING
# ============================
def decode_errors(data6, data7):
    errors = []

    # ---- Data6 ----
    if data6 & (1 << 6):
        errors.append("CAN BREAK / CAN DISCONNECTED")
    if data6 & (1 << 5):
        errors.append("RS232 BREAK")
    if data6 & (1 << 4):
        errors.append("CURRENT SENSING FAULT")
    if data6 & (1 << 3):
        errors.append("HALL SENSOR FAILURE")
    if data6 & (1 << 2):
        errors.append("TEMPERATURE PROTECTION")
    if data6 & (1 << 0):
        errors.append("WORKING MODE ERROR")

    # ---- Data7 ----
    if data7 & (1 << 7):
        errors.append("CONTROL SIGNAL ERROR")
    if data7 & (1 << 6):
        errors.append("OVERCURRENT")
    if data7 & (1 << 4):
        errors.append("UNDERVOLTAGE")
    if data7 & (1 << 3):
        errors.append("EEPROM ERROR")
    if data7 & (1 << 2):
        errors.append("HARDWARE PROTECTION")
    if data7 & (1 << 1):
        errors.append("OVERVOLTAGE")
    if data7 & (1 << 0):
        errors.append("CONTROLLER DISABLED")

    return errors

# ============================
# ERROR MONITOR THREAD
# ============================
def _error_monitor():
    global _running, error_active, last_errors

    cmd = f"candump {CAN_IFACE}"
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    while _running:
        line = process.stdout.readline()
        if not line:
            continue

        parts = line.strip().split()
        if len(parts) < 10:
            continue

        can_id = parts[1]

        if can_id.lower() != ERROR_CAN_ID:
            continue

        data = parts[-8:]
        data6 = int(data[6], 16)
        data7 = int(data[7], 16)

        errors = decode_errors(data6, data7)

        if errors:
            error_active = True
            last_errors = errors

            print("\n⚠️  CONTROLLER ERROR DETECTED ⚠️")
            print(f"CAN ID : 0x{can_id}")
            print(f"RAW    : {line.strip()}")
            for e in errors:
                print(f"  ➤ {e}")
            print("⚠️ ---------------------------\n")
        else:
            error_active = False
            last_errors = []


def start_error_listener():
    global _error_thread
    _error_thread = threading.Thread(target=_error_monitor, daemon=True)
    _error_thread.start()

def stop_error_listener():
    global _error_thread_running
    _error_thread_running = False

# ==============================
# INIT / CLEANUP
# ==============================
def init():
    start_can_interface()
    enable_absolute_position_mode()
    start_error_listener()
    print("CAN interface gestart + Absolute Position Mode ENABLED.")

def cleanup():
    stop_error_listener()
    disable_absolute_position_mode()
    stop_can_interface()
    print("CAN interface gestopt + Absolute Position Mode DISABLED.")

# Automatisch bij exit
atexit.register(cleanup)
