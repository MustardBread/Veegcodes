import Jetson.GPIO as GPIO
import time

# Gebruik fysieke pin-nummers op de header
GPIO.setmode(GPIO.BOARD)

# Pin 40 instellen als uitgang
pins = [7, 15, 33]

for pin in pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

try:
    print("Alle relais AAN")
    for pin in pins:
        GPIO.output(pin, GPIO.HIGH)
    
    time.sleep(4)

except KeyboardInterrupt:
    print("Alle relais UIT")
    for pin in pins:
        GPIO.output(pin, GPIO.LOW)

    print("Programma afgebroken door gebruiker.")

finally:
    GPIO.cleanup()
    print("GPIO opgeschoond.")
