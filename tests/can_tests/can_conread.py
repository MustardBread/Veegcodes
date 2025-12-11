import subprocess
import time
import sys
import signal
import threading
import re

# Functie om het CAN-commando te versturen
def send_command(command):
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    if result.returncode == 0:
        print(f"Command sent: {command}")
    else:
        print(f"Error sending command: {result.stderr}")

# Functie om de CAN-interface op te starten met het juiste commando
def start_can_interface():
    command = "sudo ip link set can0 up type can bitrate 250000 sjw 4 restart-ms 100 berr-reporting on"
    send_command(command)

# Functie om een decimale waarde om te zetten naar hex
def decimal_to_hex(data):
    if data < 0:
        hex_value = format(65536 + data, '04X')  # Omzetten naar een hex-waarde als het negatief is
        return hex_value
    else:
        if data > 32767:
            hex_value = format(data & 0xFFFF, '04X')  # Beperk de waarde tot een 16-bits getal
        else:
            hex_value = format(data, '04X')
        return hex_value

# Functie om de huidige positie uit te lezen
def read_position():
    """Leest de positie van de motor uit van de CAN-bus."""
    candump_process = subprocess.Popen(['candump', 'can0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        for line in candump_process.stdout:
            parts = line.split()
            if len(parts) >= 3:
                can_id = parts[1]  # CAN ID (de tweede kolom)
                
                if can_id != "05800001":
                    continue  # Sla deze regel over als het CAN ID niet gelijk is aan 05800001

                data = parts[2:]  # Data begint vanaf de derde kolom

                # Het eerste gedeelte van de data (60 04 21 01)
                first_data_part = " ".join(data[:4])  # de eerste vier getallen (60 04 21 01)
                if first_data_part != "60 04 21 01":
                    continue  # Sla deze regel over als het eerste datagedeelte niet gelijk is aan "60 04 21 01"
                
                # Het tweede gedeelte van de data
                second_data_part = " ".join(data[4:])  # de overige getallen

                # Split het tweede datagedeelte en converteer het naar een decimaal getal
                second_part_split = second_data_part.split(" ")
                if len(second_part_split) >= 2:
                    first_half = second_part_split[:2]  # bijvoorbeeld '33 02'
                    hex_value = "".join(first_half)  # Combineer de twee delen
                    swapped_value = hex_value[2:] + hex_value[:2]  # Omdraaien van de hex waarde
                    print(f"Hex value: {hex_value}, Swapped value: {swapped_value}")  # Debug: kijk naar de hex waarden
                    
                    decimal_value = int(swapped_value, 16)  # Zet de omgekeerde hex om naar een decimaal getal
                    if decimal_value > 32767:
                        decimal_value -= 65536  # Omzetten naar een negatief getal indien nodig
                    
                    print(f"Decimal value: {decimal_value}")  # Debug: zie de decimale waarde
                    
                    return decimal_value
    except KeyboardInterrupt:
        print("\nProcess interrupted. Stopping candump...")
    finally:
        candump_process.terminate()
    return None

# Functie om de motor naar een positie te sturen en te verifiëren
def move_to_position(target_position):
    hex_value = decimal_to_hex(target_position)
    base_command = "cansend can0 06000001#23.02.20.01"
    
    if target_position >= 0 and target_position <= 32767:
        full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.00.00"
    else:
        full_command = f"{base_command}.{hex_value[:2]}.{hex_value[2:]}.FF.FF"

    send_command(full_command)
    
    # Wacht een beetje voordat we de positie controleren
    time.sleep(2)
    
    # Controleer of we op de juiste positie zijn
    print(f"Checking if motor has reached position {target_position}...")
    current_position = read_position()
    if current_position is not None:
        print(f"Current position: {current_position}")
        # Verhoog de tolerantie voor de verificatie (drempel verhoogd naar 100)
        if abs(current_position - target_position) <= 100:  # Drempelwaarde verhoogd naar 100
            print(f"Motor successfully reached position {target_position}.\n")
            return True
        else:
            print(f"Motor did not reach position {target_position}. Current position is {current_position}. Retrying...\n")
            return False
    else:
        print("Failed to read position. Retrying...\n")
        return False

# Functie om een interrupt (Ctrl+C) netjes af te handelen
def signal_handler(sig, frame):
    print("\nProgram terminated by user (Ctrl+C detected).")
    send_command("sudo ip link set can0 down")
    sys.exit(0)

# Functie voor het starten van het programma
def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start de CAN-interface
    start_can_interface()
    time.sleep(2)  # Wacht een beetje totdat de interface goed opgestart is
    
    # Zet de motor in absolute position mode
    send_command("cansend can0 06000001#23.0D.20.01.00.00.00.00")
    print("\nAbsolute Position Mode enabled. Ready for input.\n")

    # Vraag de gebruiker om twee posities in te voeren
    try:
        position_1 = int(input("Enter first target position (decimal): ").strip())
        position_2 = int(input("Enter second target position (decimal): ").strip())
    except ValueError:
        print("Invalid input. Please enter valid decimal values.")
        sys.exit(1)

    # Beweeg naar de eerste positie en controleer of de motor daar is
    if move_to_position(position_1):
        # Beweeg naar de tweede positie en controleer of de motor daar is
        if move_to_position(position_2):
            print("Both positions successfully reached! Exiting...")
        else:
            print("Failed to reach second position.")
    else:
        print("Failed to reach first position.")
    
    send_command("sudo ip link set can0 down")  # Stop de CAN-interface
    print("Program completed.")

if __name__ == "__main__":
    main()
