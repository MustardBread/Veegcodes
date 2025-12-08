import Jetson.GPIO as GPIO
import time

# Gebruik fysieke pin-nummers op de header
GPIO.setmode(GPIO.BOARD)

# Pinnen instellen als uitgang
pins = [7, 15, 33]

for pin in pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        # Zet elke pin één voor één aan
        for pin in pins:
            print(f"Pin {pin} AAN")
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(1)

        # Zet alle pinnen tegelijkertijd uit
        print("Alle pinnen UIT")
        for pin in pins:
            GPIO.output(pin, GPIO.LOW)

        time.sleep(1)

except KeyboardInterrupt:
    print("\nGestopt door gebruiker.")

finally:
    # GPIO schoon afsluiten
    GPIO.cleanup()
    print("GPIO opgeschoond.")
