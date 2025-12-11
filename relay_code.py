import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

RELAY_PINS = {
    "K1": 7,
    "K2": 15,
    "K3": 33
}

# Alles standaard UIT
for pin in RELAY_PINS.values():
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

def relay_on(name):
    pin = RELAY_PINS[name]
    print(f"{name} AAN")
    GPIO.output(pin, GPIO.HIGH)

def relay_off(name):
    pin = RELAY_PINS[name]
    print(f"{name} UIT")
    GPIO.output(pin, GPIO.LOW)
