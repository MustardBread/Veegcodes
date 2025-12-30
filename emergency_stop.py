import time
import signal
import sys

import relay_code
import can_controller
import arduino_MCP4725
import oakd_fail_safe

current_speed = 0
system_on = False

# -------------------------------
#  Afsluiten met Ctrl+C
# -------------------------------
def shutdown_all():
    global current_speed
    print("\n--- Shutting down system ---")

    # ❗ EERST snelheid 0
    current_speed = 0
    arduino_MCP4725.send_speed(0)
    time.sleep(0.2)

    can_controller.send_value(0)

    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    can_controller.cleanup()
    arduino_MCP4725.close_serial()

    print("System fully stopped. Bye!")
    sys.exit(0)


def signal_handler(sig, frame):
    shutdown_all()


signal.signal(signal.SIGINT, signal_handler)

# -------------------------------
#  MAIN
# -------------------------------
def main():
    global current_speed, system_on

    print("--- System Started ---")
    print("Press Ctrl+C to stop.\n")

    can_controller.init()
    arduino_MCP4725.initialize_serial()

    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    # System inschakelen
    relay_code.relay_on("K1")   # hoofdrelais
    relay_code.relay_on("K2")   # voorwaards relay
    system_on = True

    # 🔵 Start OAK-D fail-safe thread
    oakd_fail_safe.start_camera_thread()

    # Wachten op OK
    cmd = input("Type 'ok' to start driving: ").strip().lower()
    if cmd != "ok":
        print("Aborted.")
        shutdown_all()

    # Start rijden
    current_speed = 25
    arduino_MCP4725.send_speed(current_speed)
    print("Driving FORWARD at 25% speed")

    # -------------------------------
    # LOOP
    # -------------------------------
    while True:
        if oakd_fail_safe.stop_active:
            if current_speed != 0:
                print("❌ FAIL-SAFE STOP → SPEED 0")
                current_speed = 0
                arduino_MCP4725.send_speed(0)

        time.sleep(0.05)


if __name__ == "__main__":
    main()
