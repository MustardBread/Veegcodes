import Jetson.GPIO as GPIO
import time

# Gebruik fysieke pin-nummers op de header
GPIO.setmode(GPIO.BOARD)

# Pin 40 instellen als uitgang
pins = [7, 15, 33]

for pin in pins:
    GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

print ("Alle relais AAN")
for pin in pins:
	GPIO.output(pin, GPIO.HIGH)
	
time.sleep(4)

print ("Alle relais UIT")
for pin in pins:
	GPIO.output(pin, GPIO.LOW)


GPIO.cleanup()
print("GPIO opgeschoond.")