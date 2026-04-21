import board
i2c =  board.I2C()
from adafruit_ads1x15 import ADS1115, AnalogIn, ads1x15
ads = ADS1115(i2c)
a0 = AnalogIn(ads, ads1x15.Pin.A0)
a1 = AnalogIn(ads, ads1x15.Pin.A1)
#ads.mode = Mode.CONTINUOUS
ads.gain = 2/3 # +/- 6.144V range (limited to VDD +0.3V max!)

import time

while(1):
    print(a0.value, a0.voltage)
    print(a1.value, a1.voltage)
    time.sleep(1)
