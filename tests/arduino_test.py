import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)

def send(cmd):
    ser.write((cmd + "\n").encode())
    reply =ser.readline().decode().strip()
    print("Arduino:", reply)


send("LED ON")
time.sleep(1)
send("LED OFF")

ser.close()