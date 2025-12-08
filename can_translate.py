import subprocess
import time

# Functie om het CAN-commando te versturen
def send_command(command):
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    
    if result.returncode == 0:
        print(f"Command sent: {command}")
    else:
        print(f"Error sending command: {result.stderr}")

# Functie om de huidige positie uit te lezen
def read_position():
    """Leest de positie van de motor uit van de CAN-bus."""
    candump_process = subprocess.Popen(['candump', 'can0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        for line in candump_process.stdout:
            parts = line.split()
            if len(parts) >= 3:
                can_id = parts[1]  # CAN ID (de tweede kolom)
                
                # Filteren van CAN ID's, we willen alleen data van 05800001 verwerken
                if can_id != "05800001":
                    continue  # Sla deze regel over als het CAN ID niet gelijk is aan 05800001

                data = parts[3:]  # Data begint vanaf de vierde kolom (de derde kolom is de lengte)

                # Het eerste gedeelte van de data (60 06 21 01)
                first_data_part = " ".join(data[:4])  # de eerste vier getallen (60 06 21 01)
                
                # Als het eerste datagedeelte niet overeenkomt, overslaan
                if first_data_part != "60 06 21 01":
                    continue  # Sla deze regel over als het eerste datagedeelte niet gelijk is aan "60 06 21 01"
                
                # Het tweede gedeelte van de data (bijv. 3F 03 00 00)
                second_data_part = " ".join(data[4:])  # de overige getallen

                # Nu splitsen we het tweede gedeelte van de data verder in twee delen
                second_part_split = second_data_part.split(" ")  # splitst in een lijst ['3F', '03', '00', '00']
                
                # Initialiseer de variabelen voor het geval er minder dan 4 items zijn
                first_half = ''
                second_half = ''
                
                if len(second_part_split) >= 2:
                    first_half = " ".join(second_part_split[:2])  # "3F 03"
                if len(second_part_split) >= 2:
                    second_half = " ".join(second_part_split[2:])  # "00 00"
                
                # Printen van de verschillende delen
                print(f"CAN ID: {can_id}, Eerste data gedeelte: {first_data_part}, Tweede data gedeelte: {first_half}, {second_half}")
            
                # Als het CAN ID overeenkomt met 05800001, verwerk het dan
                if can_id == "05800001" and first_data_part == "60 06 21 01":
                    # Verwijder de spaties in first_half en zet om naar een decimaal getal
                    hex_value = first_half.replace(" ", "")  # Verwijder spaties (bijv. "33 02" wordt "3302")
                    
                    # De bytes altijd omkeren
                    swapped_value = hex_value[2:] + hex_value[:2]  # Wissel de eerste twee cijfers om

                    # Zet de omgewisselde hex waarde om naar een decimaal getal
                    decimal_value = int(swapped_value, 16)  # Zet de hexadecimale string om naar een decimaal getal
                    # Als de waarde groter is dan 32767 (omdat we werken met een 16-bit getal), beschouwen we het als negatief
                    if decimal_value > 32767:
                        decimal_value -= 65536  # 65536 is 2^16, het omzetten naar een negatief getal in 2's complement
                    print(f"Hex waarde na wisselen: {swapped_value}, Decimaal: {decimal_value}")
                    
                    return decimal_value
    except KeyboardInterrupt:
        print("\nProcess interrupted. Stopping candump...")
    finally:
        candump_process.terminate()

    return None

# Functie om de motorpositie aan te vragen
def request_position():
    """Verstuurt het commando om de motorpositie aan te vragen."""
    command = "cansend can0 06000001#40.06.21.01.00.00.00.00"
    send_command(command)

# Hoofdprogramma
def main():
    while True:
        # Vraag de motorpositie aan
        request_position()
        
        # Wacht een korte tijd om de respons van de CAN-bus te krijgen
        time.sleep(1)
        
        # Lees de motorpositie
        current_position = read_position()
        if current_position is not None:
            print(f"Current motor position: {current_position}")
        else:
            print("Failed to read motor position.")
        
        # Wacht een korte tijd voordat we de positie opnieuw aanvragen
        time.sleep(2)

if __name__ == "__main__":
    main()
