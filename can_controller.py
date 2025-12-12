import subprocess
import time
import atexit

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

# ----------------------------------------------------
# EXTRA: Automatic mode control
# ----------------------------------------------------

def enable_absolute_position_mode():
    """Stuur commando om Absolute Position Mode in te schakelen."""
    send_command("cansend can0 06000001#23.0D.20.01.00.00.00.00")

def disable_absolute_position_mode():
    """Stuur commando om Absolute Position Mode uit te schakelen."""
    send_command("cansend can0 06000001#23.0C.20.01.00.00.00.00")

def init():
    """Initialisatie van CAN + mode."""
    start_can_interface()
    enable_absolute_position_mode()
    print("CAN interface gestart + Absolute Position Mode ENABLED.")

def cleanup():
    """Zorg dat mode uit gaat + interface wordt gestopt."""
    disable_absolute_position_mode()
    stop_can_interface()
    print("CAN interface gestopt + Absolute Position Mode DISABLED.")

# automatisch uitvoeren bij exit (Ctrl+C, fout, normaal einde)
atexit.register(cleanup)
