from inputs import get_gamepad, UnpluggedError
import time
import signal
import sys
sys.path.append("/home/veegmachine/Veegcodes")

import can_controller

STEER_MAX = 3000
DEADZONE = 3000

last_steer = None




def shutdown(sig=None, frame=None):
    print("\n Stoppen, stuur recht + CAN uit")

    try:
        can_controller.send_value(0)
        can_controller.stop_can_interface()
    except Exception as e:
        print("Shutdown error:", e)

    sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)


def handle_steering(raw_x):
    global last_steer

    if abs(raw_x) < DEADZONE:
        steer = 0
    else:
        steer = int((raw_x / 32767) * STEER_MAX)


    if steer != last_steer:
        can_controller.send_value(steer)
        print(f"Stuurhoek: {steer}")
        last_steer = steer


def main():
    print("Xbox controller test gestart")
    print("Linker joystick = sturen")
    print("Ctrl+C om te stoppen\n")

    can_controller.start_can_interface()
    time.sleep(0.5)

    can_controller.send_command(
        "cansend can0 06000001#23.0D.20.01.00.00.00.00"
    )

    try:
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == "ABS_X":
                    handle_steering(event.state)

    except UnpluggedError:
        print("Controller losgekoppeld")
        shutdown()

if __name__ == "__main__":
    main()
