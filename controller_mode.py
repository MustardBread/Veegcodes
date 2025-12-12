"""
controller_mode.py

Xbox controller (Logic3 PDP) -> bestuurt:
 - stuur via CAN (absolute position mode)
 - speed via arduino_MCP4725.send_speed()
 - relais via relay_code.relay_on/off()

Requirements:
  pip3 install inputs
  run as user who can read /dev/input/js0 (or run with sudo)
"""

import time
import signal
import sys
from threading import Event

from inputs import get_gamepad, UnpluggedError

import relay_code
import can_controller
import arduino_MCP4725

# -----------------------
# Config / mappings
# -----------------------
# Pas deze mappings aan als jouw controller andere event-namen geeft.
AXIS_STEER = 'ABS_X'     # left stick horizontal
AXIS_LT = 'ABS_Z'        # left trigger (soms gebruikt)
AXIS_RT = 'ABS_RZ'       # right trigger (soms used)
# Buttons (inputs uses linux evdev names)
BTN_B = 'BTN_EAST'      # B
BTN_X = 'BTN_WEST'       # X
BTN_Y = 'BTN_NORTH'      # Y

# Steering scale: joystick -> CAN decimal value
STEER_MIN = -8500
STEER_MAX = 9600
DEADZONE = 4000  # joystick deadzone in raw units (for -32768..32767)

# Speed mapping: trigger -> 0..100
# We'll detect axis output range (0..255 or -32768..32767) dynamically.

# How often to check input loop (seconds)
LOOP_DELAY = 0.01

# -----------------------
# State
# -----------------------
system_on = False
reverse = False
borstels = False
current_speed = 0
last_sent_speed = None
last_sent_steer = None

stop_event = Event()

# -----------------------
# Helpers
# -----------------------
def clamp(v, a, b):
    return max(a, min(b, v))

def map_range(x, in_min, in_max, out_min, out_max):
    # linear map with clamp
    if in_max == in_min:
        return out_min
    v = (x - in_min) / (in_max - in_min)
    return out_min + v * (out_max - out_min)

def normalize_axis(value):
    """
    Normalize typical evdev axis values to -1.0 .. 1.0 or 0..1 for triggers.
    Many joysticks give -32768..32767 for sticks, triggers may be 0..255 or -32768..32767.
    We will handle both heuristically by looking at sign/range.
    """
    # if within 0..255 -> treat as 0..255
    if 0 <= value <= 255:
        return value, 0, 255  # raw, in_min, in_max
    # else assume full signed 16-bit
    return value, -32768, 32767

def axis_to_steer(raw_value):
    raw, in_min, in_max = normalize_axis(raw_value)
    # map raw to -3000..+3000
    steer = map_range(raw, in_min, in_max, STEER_MIN, STEER_MAX)
    # apply deadzone (if stick near center, set zero)
    # compute center value
    center_raw = (in_min + in_max) / 2.0
    if abs(raw - center_raw) < DEADZONE:
        return 0
    return int(clamp(steer, STEER_MIN, STEER_MAX))

def axis_to_speed(raw_value):
    raw, in_min, in_max = normalize_axis(raw_value)
    # Some controllers map trigger 0..255 (released = 0, pressed = 255)
    # Some map -32768..32767 (released = -32768). We map to 0..100
    # If in_min < 0, treat center as in_min (released)
    if in_min < 0:
        # convert to 0..1
        v = (raw - in_min) / (in_max - in_min)
    else:
        v = (raw - in_min) / (in_max - in_min)
    speed = int(clamp(round(v * 100), 0, 100))
    return speed

# -----------------------
# Hardware init / cleanup
# -----------------------
def init_hardware():
    print("Initializing hardware...")
    try:
        can_controller.start_can_interface()
        # send absolute position mode ON once
        can_controller.send_command("cansend can0 06000001#23.0D.20.01.00.00.00.00")
        print("CAN started and Absolute Position Mode enabled.")
    except Exception as e:
        print("Warning: CAN init error:", e)

    # serial
    try:
        arduino_MCP4725.initialize_serial()
    except Exception as e:
        print("Warning: serial init error:", e)

    # Ensure relays start OFF
    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")


def cleanup_hardware():
    print("Cleaning up hardware...")
    # send absolute position mode OFF
    try:
        can_controller.send_command("cansend can0 06000001#23.0C.20.01.00.00.00.00")
        can_controller.stop_can_interface()
    except Exception as e:
        print("Warning during CAN cleanup:", e)

    try:
        arduino_MCP4725.close_serial()
    except Exception as e:
        print("Warning during serial close:", e)

    # relays off
    relay_code.relay_off("K1")
    relay_code.relay_off("K2")
    relay_code.relay_off("K3")
    print("Cleanup done.")


# -----------------------
# Signal handling
# -----------------------
def signal_handler(sig, frame):
    stop_event.set()
    cleanup_hardware()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


# -----------------------
# Event processing
# -----------------------
def process_gamepad_event(event):
    global system_on, reverse, borstels, current_speed, last_sent_speed, last_sent_steer

    # Axes
    if event.ev_type == 'Absolute':
        if event.code == AXIS_STEER:
            steer_val = axis_to_steer(event.state)
            # only send if changed significantly
            if last_sent_steer is None or abs(steer_val - last_sent_steer) > 50:
                # Only send if system_on (you wanted steering only when on)
                if system_on:
                    can_controller.send_value(steer_val)
                    last_sent_steer = steer_val
                    print(f"Steer -> {steer_val}")
        elif event.code == AXIS_RT or event.code == AXIS_LT:
            # use RT primarily, fallback to LT if RT not present
            speed_val = axis_to_speed(event.state)
            if speed_val != last_sent_speed:
                current_speed = speed_val
                if system_on:
                    arduino_MCP4725.send_speed(current_speed)
                    last_sent_speed = current_speed
                    print(f"Speed -> {current_speed}")
	#elif event.code == AXIS_LT:
	#	speed_val = axis_to_speed(event.state)
	#	if speed_val != last_sent_speed:
	#		current_speed = speed_val
	#			if system_on:
	#				arduino_MCP4725.send_speed(current_speed)
	#				last_sent_speed = current_speed
	#				print(f"Speed -> {current_speed}")
    # Buttons
    elif event.ev_type == 'Key':
        # BTN press state: 1 = pressed, 0 = released
        if event.code == BTN_B and event.state == 1:
            system_on = not system_on
            print("SYSTEM ON =", system_on)
            if system_on:
                relay_code.relay_on("K1")
            else:
                relay_code.relay_off("K1")
                # optionally stop motors when system off
                arduino_MCP4725.send_speed(0)
        elif event.code == BTN_X and event.state == 1:
            reverse = not reverse
            print("REVERSE =", reverse)
            if reverse:
                relay_code.relay_on("K2")
            else:
                relay_code.relay_off("K2")
        elif event.code == BTN_Y and event.state == 1:
            borstels = not borstels
            print("BORSTELS =", borstels)
            if borstels:
                relay_code.relay_on("K3")
            else:
                relay_code.relay_off("K3")


# -----------------------
# Main loop
# -----------------------
def main_loop():
    print("Controller mode started. Press Ctrl+C to exit.")
    while not stop_event.is_set():
        try:
            events = get_gamepad()  # blocking until events available
            for e in events:
                process_gamepad_event(e)
        except UnpluggedError:
            print("Controller unplugged - waiting for reconnect...")
            time.sleep(1)
        except Exception as ex:
            print("Error reading controller:", ex)
            time.sleep(0.2)


if __name__ == "__main__":
    init_hardware()
    try:
        main_loop()
    finally:
        cleanup_hardware()
