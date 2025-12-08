import board
import busio
import adafruit_mcp4725

i2c = busio.I2C(board.SCL, board.SDA)
dac = adafruit_mcp4725.MCP4725(i2c)

# dac.value = int(1.5 / 5.0 * 65535)

def set_percent(p): # p = 0.0 t/m 1.0
    Vmin = 1.1
    Vmax = 3.8
    Vout = Vmin + p * (Vmax - Vmin)
    dac.value = int(Vout / 5.0 * 65535)