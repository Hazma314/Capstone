import pygame
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

            if (lsv > -0.125) :
                setdir(1, "fw")
                p.ChangeDutyCycle(lsv*100)
            elif (lsv < 0.125) :
                setdir(1, "rev")
                p.ChangeDutyCycle(-lsv*100)

            if (rsv > -0.125) :
                setdir(2, "fw")
                p.ChangeDutyCycle(rsv*100)
            elif (rsv < 0.125) :
                setdir(2, "rev")
                p.ChangeDutyCycle(-rsv*100)

            time.sleep(0.1)

    except KeyboardInterrupt:
        pygame.quit()
        p.stop()
        GPIO.cleanup() 



if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()