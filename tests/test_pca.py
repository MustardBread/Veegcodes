from pca9685_no_blinka import PCA9685

import time
 
pca = PCA9685(i2c_bus=1, address=0x41, freq=50)
 
print("Running test on channel 0...")
 
while True:

    print("Duty 0%")

    pca.set_duty_cycle(0, 0)

    time.sleep(1)
 
    print("Duty 50%")

    pca.set_duty_cycle(0, 50)

    time.sleep(1)
 
    print("Duty 100%")

    pca.set_duty_cycle(0, 100)

    time.sleep(1)

 