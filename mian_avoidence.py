import time
import signal
import sys

# Hardware / besturing
import relay_code
import can_controller
import arduino_MCP4725

# Camera logica
import oakd_fail_safe          # absolute STOP
import oakd_side_avoidance     # links / rechts ontwijken


# ============================
# CONSTANTEN
# ============================
DRIVE_SPEED = 0        # %
STEER_LEFT = 9600
STEER_RIGHT = -8500
STEER_STRAIGHT = 0

AVOID_TIME = 2.0        # seconden ontwijken


# ============================
# SHUTDOWN
# ============================
def shutdown_all():
    print("\n--- SAFE SHUTDOWN ---")

    # Eerst snelheid 0
    arduino_MCP4725.send_speed(0)
    time.sleep(0.2)

    # Stuur recht
    can_controller.send_value(0)

    # Relays uit
    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    # Camera threads stoppen
    oakd_fail_safe.stop_camera()
    oakd_side_avoidance.stop_camera()

    # Interfaces afsluiten
    can_controller.cleanup()
    arduino_MCP4725.close_serial()

    print("System fully stopped.")
    sys.exit(0)


def signal_handler(sig, frame):
    shutdown_all()


signal.signal(signal.SIGINT, signal_handler)


# ============================
# MAIN
# ============================
def main():

    print(">>> Veegmachine START <<<")

    # ---------- INIT ----------
    can_controller.init()
    arduino_MCP4725.initialize_serial()

    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    # Camera threads
    oakd_fail_safe.start_camera_thread()
    oakd_side_avoidance.start_camera_thread()

    input("Type 'ok' en druk ENTER om te starten...")

    # System ON
    relay_code.relay_on("K2")
    arduino_MCP4725.send_speed(DRIVE_SPEED)
    can_controller.send_value(STEER_STRAIGHT)

    print(">>> Rijdt vooruit op 30% <<<")

    avoid_direction = None
    avoid_start_time = 0.0

    while True:
        now = time.time()

        # ===================================
        # FAIL SAFE → ALTIJD PRIORITEIT
        # ===================================
        if oakd_fail_safe.stop_active:
            arduino_MCP4725.send_speed(0)
            can_controller.send_value(STEER_STRAIGHT)
            time.sleep(0.05)
            continue

        # ===================================
        # ACTIEVE ONTWIJKING
        # ===================================
        if avoid_direction is not None:
            if now - avoid_start_time >= AVOID_TIME:
                # Ontwijking klaar → rechtuit
                avoid_direction = None
                can_controller.send_value(STEER_STRAIGHT)
            else:
                time.sleep(0.05)
                continue

        # ===================================
        # NIEUWE ONTWIJKING STARTEN
        # ===================================
        if oakd_side_avoidance.obstacle_left:
            print("Obstacle LEFT → stuur RIGHT")
            can_controller.send_value(STEER_RIGHT)
            avoid_direction = "right"
            avoid_start_time = now
            continue

        if oakd_side_avoidance.obstacle_right:
            print("Obstacle RIGHT → stuur LEFT")
            can_controller.send_value(STEER_LEFT)
            avoid_direction = "left"
            avoid_start_time = now
            continue

        # ===================================
        # NORMAAL RIJDEN
        # ===================================
        arduino_MCP4725.send_speed(DRIVE_SPEED)
        can_controller.send_value(STEER_STRAIGHT)

        time.sleep(0.05)


# ============================
# ENTRY POINT
# ============================
if __name__ == "__main__":
    main()
