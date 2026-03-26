import pygame
import time

pygame.init()

#pygame.joystick.init()
print(pygame.joystick.get_count())
try:
    while(1):
        pygame.event.get()
        controller = pygame.joystick.Joystick(0)
        a0 = controller.get_axis(0)
        a1 = controller.get_axis(1)
        a3 = controller.get_axis(3)
        a4 = controller.get_axis(4)
        print(f"0: {a0:>6.3f} 1: {a1:>6.3f} 3: {a3:>6.3f} 4: {a4:>6.3f}\n")
        print("\n")
        time.sleep(0.1)

except KeyboardInterrupt:
    pygame.quit()
