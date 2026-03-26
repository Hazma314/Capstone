import pygame

pygame.init()

def main():

    # This dict can be left as-is, since pygame will generate a
    # pygame.JOYDEVICEADDED event for every joystick connected
    # at the start of the program.
    joysticks = {}

    while(1):
        a0 = joysticks.get_axis(0)
        a1 = joysticks.get_axis(1)
        a2 = joysticks.get_axis(2)
        a3 = joysticks.get_axis(3)

        print(f"0: {a0:>6.3f} 1: {a1:>6.3f} 2: {a2:>6.3f} 3: {a3:>6.3f}\n")


if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()