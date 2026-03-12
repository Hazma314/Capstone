import RPi.GPIO as GPIO
import time

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
p.start(0)

print("pwm start")

try:
    while (1) :
        setdir(1, "fw")
        print("fw")
        p.ChangeDutyCycle(100)
        print("dc: 100")
        time.sleep(1)
        p.ChangeDutyCycle(0)
        print("dc: 0")
        time.sleep(1)
        setdir(1, "rev")
        print("rev")
        p.ChangeDutyCycle(100)
        time.sleep(1)
        p.ChangeDutyCycle(0)
        time.sleep(1)

except KeyboardInterrupt:
    print("stopping")
    p.stop()