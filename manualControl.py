import pygame
import RPi.GPIO as GPIO
import time

#init adc
import board
i2c =  board.I2C()
from adafruit_ads1x15 import ADS1115, AnalogIn, ads1x15
ads = ADS1115(i2c)
a0 = AnalogIn(ads, ads1x15.Pin.A0)
a1 = AnalogIn(ads, ads1x15.Pin.A1)
#ads.mode = Mode.CONTINUOUS       DOES NOT WORK
ads.gain = 2/3 # +/- 6.144V range (limited to VDD +0.3V max!)

#human readable pin names
act = {
    1: {"a": 29, "b": 31, "en": 32},
    2: {"a": 16, "b": 18, "en": 33},
}

#define, enable pi pins
GPIO.setmode(GPIO.BOARD)
for act_num, pins in act.items():
    GPIO.setup(pins['a'], GPIO.OUT)
    GPIO.output(pins['a'], GPIO.LOW)
    GPIO.setup(pins['b'], GPIO.OUT)
    GPIO.output(pins['b'], GPIO.LOW)
    GPIO.setup(pins['en'], GPIO.OUT)

print("pindef done")

def setdir (actuator, dir) :
    pins = act.get(actuator)
    if dir == "fw" :
        GPIO.output(pins['a'], GPIO.LOW)
        GPIO.output(pins['b'], GPIO.HIGH)
    if dir == "rev" :
        GPIO.output(pins['a'], GPIO.HIGH)
        GPIO.output(pins['b'], GPIO.LOW)

#init pwm for enable pins
p = GPIO.PWM(act[1]['en'], 100)
q = GPIO.PWM(act[2]['en'], 100)
p.start(0)
q.start(0)

print("pwm start")

pygame.init()

def main():
    try:
        while(1):
            pygame.event.get()
            controller = pygame.joystick.Joystick(0)
            lsv = controller.get_axis(1) #left stick vertical
            rsv = controller.get_axis(4) #right stick vertical
            print(f"1: {lsv:>6.3f} 4: {rsv:>6.3f}\n")
            print("\n")

            if (lsv < -0.125) :
                setdir(1, "rev")
                p.ChangeDutyCycle(abs(lsv)*100)
            elif (lsv > 0.125) :
                setdir(1, "fw")
                p.ChangeDutyCycle(lsv*100)
            
            # return to netural if stick is near center
            # untested and not implemented until pots are confirmed working
            #
            # if (abs(lsv) <= 0.125) :
            #     if (a0.value > 10000) :
            #         setdir(1, "fw")
            #         p.ChangeDutyCycle((a0.value/65535)*100) 
            #     elif (a0.value < 5000) :
            #         setdir(1, "rev")
            #         p.ChangeDutyCycle((1-(a0.value/65535))*100)

            if (rsv < -0.125) :
                setdir(2, "fw")
                q.ChangeDutyCycle(abs(rsv)*100)
            elif (rsv > 0.125) :
                setdir(2, "rev")
                q.ChangeDutyCycle(abs(rsv)*100)

            # see above comment block
            #
            # if (abs(rsv) <= 0.125) :
            #     if (a1.value > 10000) :
            #         setdir(2, "fw")
            #         q.ChangeDutyCycle((a1.value/65535)*100)
            #     elif (a1.value < 5000) :
            #         setdir(2, "rev")
            #         q.ChangeDutyCycle((1-(a1.value/65535))*100)

            time.sleep(0.01)

    except KeyboardInterrupt:
        pygame.quit()
        p.stop()
        GPIO.cleanup() 



if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()
