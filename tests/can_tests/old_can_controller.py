import subprocess
import time
import sys
import signal

def send_command(command):
    """Functie om het CAN-commando te versturen."""
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    if result.returncode == 0:
        print(f"Command sent: {command}")
    else:
        print(f"Error sending command: {result.stderr}")

def start_can_interface():
    """Functie om de CAN-interface op te starten met het juiste commando."""
    command = "sudo ip link set can0 up type can bitrate 250000 sjw 4 restart-ms 100 berr-reporting on"
    send_command(command)

def decimal_to_hex(data):
    """Functie om een decimale waarde om te zetten naar een hexadecimale waarde in de juiste lengte."""
    if data < 0:
        hex_value = format(65536 + data, '04X')
        return hex_value
    else:
        if data > 32767:
            hex_value = format(data & 0xFFFF, '04X')
        else:
            hex_value = format(data, '04X')
        return hex_value

def process_input():
    """Functie om decimale input te verwerken en het commando te sturen."""
    while True:
        dec_value = input("\nEnter decimal value (press Enter when done, or 'l' to stop): ").strip()

        if dec_value.lower() == 'l':
            send_command("cansend can0 06000001#23.0C.20.01.00.00.00.00")
            send_command("sudo ip link set can0 down")
            print("\nCommands executed. Exiting...\n")
            sys.exit(0)

        elif dec_value == "":
            break

        try:
            # Probeer de invoer om te zetten naar een integer
            dec_value = int(dec_value)

            # Zet de decimale waarde om naar hex
            hex_value = decimal_to_hex(dec_value)

            # Maak het volledige CAN-commando op
            base_command = "cansend can0 06000001#23.02.20.01"
            
            if dec_value >= 0 and dec_value <= 32767:
                full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.00.00"
            else:
                full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.FF.FF"

            # Verstuur het commando
            send_command(full_command)

        except ValueError:
            print("\nInvalid input. Please enter a valid decimal value.")

def signal_handler(sig, frame):
    """Functie om de signalen van Ctrl+C op te vangen."""
    print("\nProgram terminated by user (Ctrl+C detected).")
    send_command("sudo ip link set can0 down")  # Optioneel: uitschakelen van CAN-interface
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    start_can_interface()
    time.sleep(2)  # Even wachten zodat de interface goed up is
    send_command("cansend can0 06000001#23.0D.20.01.00.00.00.00")
    print("\nAbsolute Position Mode enabled. Ready for input.")
    
    # Continu wacht op invoer van de gebruiker
    process_input()

if __name__ == "__main__":
    main()
