#!/usr/bin/env python3
"""
Read GPS coordinates from a u-blox USB receiver and print them (no logging).
"""

import argparse
import serial


def nmea_to_decimal(value, direction):
    if not value or not direction:
        return None

    try:
        raw = float(value)
    except ValueError:
        return None

    degrees = int(raw // 100)
    minutes = raw - (degrees * 100)
    decimal = degrees + (minutes / 60.0)

    if direction in ("S", "W"):
        decimal *= -1

    return decimal


def parse_line(line):
    if not line.startswith("$"):
        return None

    parts = line.strip().split(",")

    # GGA sentence (has altitude)
    if parts[0].endswith("GGA") and len(parts) > 9:
        lat = nmea_to_decimal(parts[2], parts[3])
        lon = nmea_to_decimal(parts[4], parts[5])
        alt = parts[9]

        if lat and lon:
            return lat, lon, alt

    # RMC sentence (no altitude, but good fallback)
    if parts[0].endswith("RMC") and len(parts) > 6 and parts[2] == "A":
        lat = nmea_to_decimal(parts[3], parts[4])
        lon = nmea_to_decimal(parts[5], parts[6])

        if lat and lon:
            return lat, lon, None

    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, help="Serial port (e.g. COM3 or /dev/ttyACM0)")
    parser.add_argument("--baudrate", type=int, default=9600)
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baudrate, timeout=1)

    print(f"Reading GPS from {args.port} (Ctrl+C to stop)\n")

    try:
        while True:
            line = ser.readline().decode("ascii", errors="ignore").strip()
            result = parse_line(line)

            if result:
                lat, lon, alt = result
                if alt:
                    print(f"Lat: {lat:.6f}, Lon: {lon:.6f}, Alt: {alt} m")
                else:
                    print(f"Lat: {lat:.6f}, Lon: {lon:.6f}")

    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()