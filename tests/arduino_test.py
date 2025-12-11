import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)  # IMPORTANT: allow Arduino to reset

for v in [0, 50, 100]:
    ser.write(f"{v}\n".encode())
    print("Sent:", v)
    time.sleep(1)

time.sleep(5)
ser.write(f"{0}\n".encode())
print("Sent:", 0)
    


ser.close()
