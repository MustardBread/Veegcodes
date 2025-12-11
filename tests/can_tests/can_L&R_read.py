import subprocess

# Start de candump subprocess om live data van can0 te lezen
candump_process = subprocess.Popen(['candump', 'can0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Leest de output van candump lijn voor lijn
try:
    for line in candump_process.stdout:
        parts = line.split()
        if len(parts) >= 3:
            can_id = parts[1]  # CAN ID (de tweede kolom)
            
            # Filteren van CAN ID's, we willen alleen data van 05800001 verwerken
            if can_id != "05800001":
                continue  # Sla deze regel over als het CAN ID niet gelijk is aan 05800001

            data = parts[2:]  # Data begint vanaf de derde kolom, en bevat de lengte van de data
            if data[0].startswith('['):  # De eerste kolom bevat de lengte, dus we verwijderen dit
                data = data[1:]  # Verwijder de lengte (bijv. [8])

            # Het eerste gedeelte van de data (60 04 21 01)
            first_data_part = " ".join(data[:4])  # de eerste vier getallen (60 04 21 01)
            
            # Als het eerste datagedeelte niet overeenkomt, overslaan
            if first_data_part != "60 04 21 01":
                continue  # Sla deze regel over als het eerste datagedeelte niet gelijk is aan "60 04 21 01"
            
            # Het tweede gedeelte van de data (bijv. 33 02 00 00)
            second_data_part = " ".join(data[4:])  # de overige getallen

            # Nu splitsen we het tweede gedeelte van de data verder in twee delen
            second_part_split = second_data_part.split(" ")  # splitst in een lijst ['33', '02', '00', '00']
            
            # Initialiseer de variabelen voor het geval er minder dan 4 items zijn
            first_half = ''
            second_half = ''
            
            if len(second_part_split) >= 2:
                first_half = " ".join(second_part_split[:2])  # "33 02"
            if len(second_part_split) >= 2:
                second_half = " ".join(second_part_split[2:])  # "00 00"
            
            # Printen van de verschillende delen
            print(f"CAN ID: {can_id}, Eerste data gedeelte: {first_data_part}, Tweede data gedeelte: {first_half}, {second_half}")
        
            # Als het CAN ID overeenkomt met 05800001, verwerk het dan
            if can_id == "05800001" and first_data_part == "60 04 21 01":
                if first_half == "0A DE":
                    print("Op positie, Rechts")
                elif first_half == "E2 24":
                    print("Op positie, Links")  
        
except KeyboardInterrupt:
    # Zorg ervoor dat het proces netjes wordt afgesloten bij een interrupt (CTRL+C)
    print("\nProcess interrupted. Stopping candump...")

finally:
    # Sluit de candump subprocess af
    candump_process.terminate()
