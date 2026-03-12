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

def setdir (actuator, dir) :
    pins = act.get(actuator)
    if dir == "fw" :
        GPIO.output(pins['a'], GPIO.HIGH)
        GPIO.output(pins['b'], GPIO.LOW)
    if dir == "rev" :
        GPIO.output(pins['a'], GPIO.LOW)
        GPIO.output(pins['b'], GPIO.HIGH)

#init pwm for enable pins
p = GPIO.PWM(pins['en'],100)
p.start(0)

try:
    while (1) :
        setdir(1, "fw")
        print("fw")
        p.ChangeDutyCycle(100)
        time.sleep(1000)
        p.ChangeDutyCycle(0)
        time.sleep(1000)
        setdir(1, "rev")
        print("rev")
        p.ChangeDutyCycle(100)
        time.sleep(1000)
        p.ChangeDutyCycle(0)
        time.sleep(1000)

except KeyboardInterrupt:
    print("stopping")
    p.stop()