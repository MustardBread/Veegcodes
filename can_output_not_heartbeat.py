import subprocess

# Start de candump subprocess om live data van can0 te lezen
candump_process = subprocess.Popen(['candump', 'can0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Leest de output van candump lijn voor lijn
try:
    for line in candump_process.stdout:
        parts = line.split()
        if len(parts) >= 3:
            can_id = parts[1]  # CAN ID (de tweede kolom)

            # Als het CAN ID overeenkomt met 05800001, verwerk het dan
            if can_id != "07000001":
                data = ' '.join(parts[3:])  # Data (de laatste kolom)
                print(f"CAN ID: {can_id}, Data: {data}")
        
except KeyboardInterrupt:
    # Zorg ervoor dat het proces netjes wordt afgesloten bij een interrupt (CTRL+C)
    print("\nProcess interrupted. Stopping candump...")

finally:
    # Sluit de candump subprocess af
    candump_process.terminate()
