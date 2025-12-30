import subprocess

# Start de candump subprocess om live data van can0 te lezen
candump_process = subprocess.Popen(['candump', 'can0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
def send_command(command):
    """Verstuur een CAN-commando via de terminal."""
    command = "sudo ip link set can0 up type can bitrate 250000 sjw 4 restart-ms 100 berr-reporting on"
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode == 0:
        print(f"Command sent: {command}")
    else:
        print(f"Error sending command: {result.stderr}")


# Leest de output van candump lijn voor lijn
try:
    for line in candump_process.stdout:
        parts = line.split()
        if len(parts) >= 3:
            can_id = parts[1]  # CAN ID (de tweede kolom)

            # Als het CAN ID, verwerk het dan
            if can_id != "07000001":
                data = ' '.join(parts[3:])  # Data (de laatste kolom)
                print(f"CAN ID: {can_id}, Data: {data}")
        
except KeyboardInterrupt:
    # Zorg ervoor dat het proces netjes wordt afgesloten bij een interrupt (CTRL+C)
    print("\nProcess interrupted. Stopping candump...")

finally:
    # Sluit de candump subprocess af
    candump_process.terminate()
