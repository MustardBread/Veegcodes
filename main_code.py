import time
import signal
import sys

# Jouw bestanden importeren
import relay_code
import can_controller
import arduino_MCP4725   # jouw serial bestand

# Variabelen
reverse = False
borstels = False
system_on = False
current_speed = 0  # 0 t/m 100


# -------------------------------
#  Afsluiten met Ctrl+C
# -------------------------------
def shutdown_all():
    print("\n--- Shutting down system ---")

    # Relays uit
    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    # CAN interface stoppen
    can_controller.stop_can_interface()

    # Arduino serial sluiten
    arduino_MCP4725.close_serial()

    print("System fully stopped. Bye!")
    sys.exit(0)


def signal_handler(sig, frame):
    shutdown_all()


signal.signal(signal.SIGINT, signal_handler)


# -------------------------------
#  Toepassen van variabelen
# -------------------------------
def apply_speed():
    """Stuur speed naar Arduino (0–100)."""
    global current_speed
    arduino_MCP4725.send_speed(current_speed)


def apply_reverse():
    """Reverse → bedient relais K2."""
    if reverse:
        relay_code.relay_on("K2")
        arduino_MCP4725.send_speed(0)
    else:
        relay_code.relay_off("K2")
        arduino_MCP4725.send_speed(0)


def apply_borstels():
    """Borstels → bedient relais K3."""
    if borstels:
        relay_code.relay_on("K3")
    else:
        relay_code.relay_off("K3")


def apply_system_on():
    """System ON → K1 aan + reverse/borstels toepassen."""
    if system_on:
        relay_code.relay_on("K1")
        apply_reverse()
        apply_borstels()
    else:
        relay_code.relay_off("K1")
        relay_code.relay_off("K2")
        relay_code.relay_off("K3")


# -------------------------------
#  MAIN LOOP
# -------------------------------
def main():
    global system_on, reverse, borstels, current_speed

    print("--- System Started ---")
    print("Press Ctrl+C to stop.\n")

    # CAN interface aanzetten
    can_controller.start_can_interface()

    # Arduino serial openen (direct opstarten)
    arduino_MCP4725.initialize_serial()

    # Alles begint UIT
    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    system_on = False

    while True:
        cmd = input("Command (speed / left / right / on / off / reverse / borstels): ").strip().lower()

        # ---------------- SPEED ----------------
        if cmd.isdigit():
            value = int(cmd)
            if 0 <= value <= 100:
                current_speed = value
                apply_speed()
            else:
                print("Speed must be 0–100.")

        # ------------- POSITION RIGHT ----------
        elif cmd == "right":
            can_controller.send_value(+3000)
            print("Turning RIGHT")

        # ------------- POSITION LEFT -----------
        elif cmd == "left":
            can_controller.send_value(-3000)
            print("Turning LEFT")

        # ------------- SYSTEM ON/OFF -----------
        elif cmd == "on":
            system_on = True
            apply_system_on()

        elif cmd == "off":
            system_on = False
            apply_system_on()

        # ------------- REVERSE -----------------
        elif cmd == "reverse":
            reverse = not reverse
            print(f"Reverse = {reverse}")
            apply_reverse()

        # ------------- BORSTELS ----------------
        elif cmd == "borstels":
            borstels = not borstels
            print(f"Borstels = {borstels}")
            apply_borstels()

        else:
            print("Unknown command.")

        time.sleep(0.05)


if __name__ == "__main__":
    main()
