import subprocess
import time

def send_command(command):
    """Verstuur een CAN-commando via de terminal."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print(f"Command sent: {command}")
    else:
        print(f"Error sending command: {result.stderr}")

def start_can_interface():
    """Start de CAN-interface"""
    command = "sudo ip link set can0 up type can bitrate 250000 sjw 4 restart-ms 100 berr-reporting on"
    send_command(command)
    time.sleep(1)

def stop_can_interface():
    """Stop de CAN-interface"""
    command = "sudo ip link set can0 down"
    send_command(command)

def decimal_to_hex(data):
    """Zet decimale waarde om naar hex in juiste formaat"""
    if data < 0:
        hex_value = format(65536 + data, '04X')
    else:
        if data > 32767:
            hex_value = format(data & 0xFFFF, '04X')
        else:
            hex_value = format(data, '04X')
    return hex_value

def send_value(dec_value):
    """Verstuur een decimale waarde als CAN-bericht"""
    hex_value = decimal_to_hex(dec_value)
    base_command = "cansend can0 06000001#23.02.20.01"
    if 0 <= dec_value <= 32767:
        full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.00.00"
    else:
        full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.FF.FF"
    send_command(full_command)
