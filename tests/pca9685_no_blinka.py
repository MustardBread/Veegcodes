import time

from smbus2 import SMBus
 
# PCA9685 registers

MODE1       = 0x00

PRESCALE    = 0xFE
 
LED0_ON_L   = 0x06
 
class PCA9685:

    def __init__(self, i2c_bus=1, address=0x41, freq=50):

        self.address = address

        self.bus = SMBus(i2c_bus)
 
        # Reset PCA9685

        self.write8(MODE1, 0x00)
 
        # Set PWM frequency

        self.set_pwm_freq(freq)
 
    def write8(self, reg, value):

        self.bus.write_byte_data(self.address, reg, value)
 
    def read8(self, reg):

        return self.bus.read_byte_data(self.address, reg)
 
    def set_pwm_freq(self, freq_hz):

        prescale_val = int(25000000.0 / (4096.0 * freq_hz) - 1)
 
        old_mode = self.read8(MODE1)

        new_mode = (old_mode & 0x7F) | 0x10  # sleep
 
        self.write8(MODE1, new_mode)        # go to sleep

        self.write8(PRESCALE, prescale_val)

        self.write8(MODE1, old_mode)

        time.sleep(0.005)

        self.write8(MODE1, old_mode | 0x80)  # restart
 
    def set_pwm(self, channel, on, off):

        reg = LED0_ON_L + 4 * channel

        self.bus.write_i2c_block_data(self.address, reg, [

            on & 0xFF,

            (on >> 8) & 0xFF,

            off & 0xFF,

            (off >> 8) & 0xFF,

        ])
 
    def set_duty_cycle(self, channel, duty):

        """

        duty: 0–100 (%)

        """

        duty = max(0, min(100, duty))

        off_val = int((duty / 100.0) * 4095)

        self.set_pwm(channel, 0, off_val)

 