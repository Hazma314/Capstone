import os
import time
from math import cos, sin, pi, floor
import pygame
from rplidar import RPLidar, RPLidarException  # <-- Roboticia driver

# Set up pygame and the display
os.putenv("SDL_FBDEV", "/dev/fb1")
pygame.init()
lcd = pygame.display.set_mode((320, 240))
pygame.mouse.set_visible(False)
lcd.fill((0, 0, 0))
pygame.display.update()

PORT_NAME = "/dev/ttyUSB0"
lidar = RPLidar(PORT_NAME, baudrate=115200, timeout=1)  # <-- ctor differs :contentReference[oaicite:2]{index=2}

max_distance = 0
scan_data = [0] * 360

def process_data(data):
    global max_distance
    lcd.fill((0, 0, 0))
    for angle in range(360):
        distance = data[angle]
        if distance > 0:
            max_distance = max([min([5000, distance]), max_distance])
            radians = angle * pi / 180.0
            x = distance * cos(radians)
            y = distance * sin(radians)
            point = (
                160 + int(x / max_distance * 119),
                120 + int(y / max_distance * 119),
            )
            if 0 <= point[0] < 320 and 0 <= point[1] < 240:
                lcd.set_at(point, pygame.Color(255, 255, 255))
    pygame.display.update()

try:
    # Helpful: clear any junk bytes before first command
    lidar.clean_input()  # Roboticia API :contentReference[oaicite:3]{index=3}
    time.sleep(0.1)

    print(lidar.get_info())    # Roboticia API :contentReference[oaicite:4]{index=4}
    print(lidar.get_health())  # Roboticia API :contentReference[oaicite:5]{index=5}

    # iter_scans yields list of (quality, angle, distance) :contentReference[oaicite:6]{index=6}
    for scan in lidar.iter_scans(min_len=5):
        for (quality, angle, distance) in scan:
            scan_data[min(359, floor(angle))] = distance
        process_data(scan_data)

except KeyboardInterrupt:
    print("Stopping.")

except RPLidarException as e:
    # If you still get occasional framing errors, this is a decent recovery pattern:
    print("Lidar error:", e)
    try:
        lidar.stop()
        lidar.stop_motor()
        lidar.clear_input()
        lidar.reset()  # resets the core :contentReference[oaicite:7]{index=7}
    except Exception:
        pass

finally:
    try:
        lidar.stop()
    except Exception:
        pass
    try:
        lidar.stop_motor()
    except Exception:
        pass
    try:
        lidar.disconnect()
    except Exception:
        pass
