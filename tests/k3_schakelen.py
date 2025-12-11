import Jetson.GPIO as GPIO
import time

# Gebruik fysieke pin-nummers op de header
GPIO.setmode(GPIO.BOARD)

# Pinnen instellen als uitgang
pins = [7]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

try:
    while True:
        # Vraag de gebruiker om input
        user_input = input("Typ 'on' om pin 7 aan te zetten, 'off' om uit te zetten, of 'exit' om het programma te stoppen: ").lower()

        if user_input == 'on':
            print("Pin 7 AAN")
            GPIO.output(7, GPIO.HIGH)  # Zet pin  aan
        elif user_input == 'off':
            print("Pin 7 UIT")
            GPIO.output(7, GPIO.LOW)  # Zet pin  uit
        elif user_input == 'exit':
            print("Programma gestopt door gebruiker.")
            break
        else:
            print("Ongeldige invoer, probeer 'on', 'off' of 'exit'.")

except KeyboardInterrupt:
    print("\nGestopt door gebruiker.")

finally:
    # GPIO schoon afsluiten
    GPIO.cleanup()
    print("GPIO opgeschoond.")
