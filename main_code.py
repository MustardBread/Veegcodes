import time
import signal
import sys
import can_test_controller
from relay_code import relay_on, relay_off

RUNNING = True

def signal_handler(sig, frame):
    """Wordt uitgevoerd bij Ctrl+C."""
    global RUNNING
    print("\nCtrl+C gedetecteerd – systeem wordt netjes afgesloten...")
    # Relais uit
    relay_off("K1")
    relay_off("K2")
    print("Relais uitgeschakeld")
    # CAN-interface uit
    can_test_controller.stop_can_interface()
    print("CAN interface gestopt")
    RUNNING = False
    sys.exit(0)

def setup():
    """Start CAN, relais en stuur absolute mode op."""
    print("Systeem starten...")
    # Start CAN
    can_test_controller.start_can_interface()
    # Absolute Position Mode éénmalig sturen
    can_test_controller.send_command("cansend can0 06000001#23.0D.20.01.00.00.00.00")
    print("Absolute Position Mode Enabled")
    # Relais aan
    relay_on("K1")
    relay_on("K2")
    print("Relais K1 en K2 ingeschakeld\n")

def main_loop():
    """Hoofdlus – stuurt geen CAN berichten meer automatisch."""
    print("Main code draait – alles blijft aan. Ctrl+C om af te sluiten.\n")
    while RUNNING:
        # Niets doen, alleen “aan” blijven
        time.sleep(0.5)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    setup()
    main_loop()
