import time
import signal
import sys

# ============================
# Hardware / besturing
# ============================
import relay_code
import can_controller
import arduino_MCP4725

# ============================
# Camera logica
# ============================
import oakd_side_avoidance


# ============================
# CONSTANTEN
# ============================
DRIVE_SPEED = 25
AVOID_SPEED = 15
REVERSE_SPEED = 30

STEER_LEFT = 9000
STEER_RIGHT = -9000
STEER_STRAIGHT = 0

AVOID_TIME = 2.0
REVERSE_TIME = 4.0
RECOVERY_TIME = 0.7   # blind rechtdoor na manoeuvre


# ============================
# CAMERA CONFIGURATIE
# ============================
SIDE_AVOIDANCE_CONFIG = {
    "SIDE_DISTANCE": 1000,
    "SIDE_RATIO_THRESHOLD": 0.03,
    "TOP_IGNORE_RATIO": 0.05,
    "BOTTOM_IGNORE_RATIO": 0.10,
    "SHOW_DEBUG": True
}


# ============================
# SHUTDOWN
# ============================
def shutdown_all():
    print("\n--- SAFE SHUTDOWN ---")

    arduino_MCP4725.send_speed(0)
    time.sleep(0.2)

    can_controller.send_value(STEER_STRAIGHT)

    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")

    oakd_side_avoidance.stop_camera()

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

    relay_code.relay_on("K1")
    relay_code.relay_on("K2")

    oakd_side_avoidance.start_camera_thread(SIDE_AVOIDANCE_CONFIG)

    input("Type 'ok' en druk ENTER om te starten...")

    # ============================
    # STATE TRACKING
    # ============================
    last_speed = None
    last_steer = None

    def set_speed(value):
        nonlocal last_speed
        if value != last_speed:
            arduino_MCP4725.send_speed(value)
            last_speed = value

    def set_steer(value):
        nonlocal last_steer
        if value != last_steer:
            can_controller.send_value(value)
            last_steer = value

    set_speed(DRIVE_SPEED)
    set_steer(STEER_STRAIGHT)

    # ============================
    # STATE MACHINE
    # ============================
    state = "FORWARD"
    state_start_time = time.time()

    reverse_left_sum = 0.0
    reverse_right_sum = 0.0
    reverse_samples = 0

    print(">>> Rijdt vooruit <<<")

    # ============================
    # LOOP
    # ============================
    while True:
        now = time.time()

        # ============================
        # REVERSE
        # ============================
        if state == "REVERSE":
            left = oakd_side_avoidance.left_distance
            right = oakd_side_avoidance.right_distance

            if left > 0 and right > 0:
                reverse_left_sum += left
                reverse_right_sum += right
                reverse_samples += 1

            if now - state_start_time >= REVERSE_TIME:
                set_speed(0)
                time.sleep(0.2)

                relay_code.relay_on("K2")  # vooruit
                time.sleep(0.2)

                avg_left = reverse_left_sum / reverse_samples if reverse_samples else 0
                avg_right = reverse_right_sum / reverse_samples if reverse_samples else 0

                print(f"Reverse meting → L: {avg_left:.0f} mm | R: {avg_right:.0f} mm")

                if avg_left > avg_right:
                    print("→ Draai LINKS")
                    set_steer(STEER_LEFT)
                else:
                    print("→ Draai RECHTS")
                    set_steer(STEER_RIGHT)

                set_speed(DRIVE_SPEED)

                state = "RECOVERY"
                state_start_time = now

            time.sleep(0.05)
            continue

        # ============================
        # AVOID
        # ============================
        if state == "AVOID":
            if now - state_start_time >= AVOID_TIME:
                set_steer(STEER_STRAIGHT)
                set_speed(DRIVE_SPEED)

                state = "RECOVERY"
                state_start_time = now

            time.sleep(0.05)
            continue

        # ============================
        # RECOVERY (blind)
        # ============================
        if state == "RECOVERY":
            set_speed(DRIVE_SPEED)
            set_steer(STEER_STRAIGHT)

            if now - state_start_time >= RECOVERY_TIME:
                state = "FORWARD"

            time.sleep(0.05)
            continue

        # ============================
        # FORWARD (beslissen)
        # ============================
        if oakd_side_avoidance.obstacle_left and oakd_side_avoidance.obstacle_right:
            print("Obstacle LINKS + RECHTS → achteruit")

            set_speed(0)
            time.sleep(0.2)

            relay_code.relay_off("K2")
            time.sleep(0.2)

            set_speed(REVERSE_SPEED)

            reverse_left_sum = 0.0
            reverse_right_sum = 0.0
            reverse_samples = 0

            state = "REVERSE"
            state_start_time = now
            continue

        if oakd_side_avoidance.obstacle_left:
            print("Obstacle LEFT → stuur RIGHT")
            set_steer(STEER_RIGHT)
            set_speed(AVOID_SPEED)

            state = "AVOID"
            state_start_time = now
            continue

        if oakd_side_avoidance.obstacle_right:
            print("Obstacle RIGHT → stuur LEFT")
            set_steer(STEER_LEFT)
            set_speed(AVOID_SPEED)

            state = "AVOID"
            state_start_time = now
            continue

        # Normaal rijden
        set_speed(DRIVE_SPEED)
        set_steer(STEER_STRAIGHT)

        time.sleep(0.05)


# ============================
# ENTRY POINT
# ============================
if __name__ == "__main__":
    main()
