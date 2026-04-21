#!/usr/bin/env python3
"""
Log GPS coordinates from a u-blox USB-connected receiver to CSV.

Tested approach:
- Reads NMEA sentences from a serial port
- Parses GGA and RMC messages
- Writes timestamp, latitude, longitude, altitude, fix info to CSV

Install:
    pip install pyserial

Find your port:
    python -m serial.tools.list_ports

Examples:
    python gps_logger.py --port COM3
    python gps_logger.py --port /dev/ttyACM0 --output gps_log.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

import serial


def nmea_to_decimal(value: str, direction: str) -> Optional[float]:
    """
    Convert NMEA coordinate format to decimal degrees.

    Latitude comes as ddmm.mmmm
    Longitude comes as dddmm.mmmm
    """
    if not value or not direction:
        return None

    try:
        raw = float(value)
    except ValueError:
        return None

    if direction in ("N", "S"):
        degrees = int(raw // 100)
        minutes = raw - (degrees * 100)
    elif direction in ("E", "W"):
        degrees = int(raw // 100)
        minutes = raw - (degrees * 100)
    else:
        return None

    decimal = degrees + (minutes / 60.0)

    if direction in ("S", "W"):
        decimal *= -1.0

    return decimal


def parse_gga(fields: list[str]) -> Optional[dict]:
    """
    Parse GGA sentence fields.

    Example:
    $GPGGA,time,lat,NS,lon,EW,fix_quality,num_sats,hdop,alt,M,...
    """
    if len(fields) < 10:
        return None

    lat = nmea_to_decimal(fields[2], fields[3])
    lon = nmea_to_decimal(fields[4], fields[5])

    if lat is None or lon is None:
        return None

    fix_quality = fields[6] or ""
    num_sats = fields[7] or ""
    hdop = fields[8] or ""
    altitude = fields[9] or ""

    return {
        "source": "GGA",
        "latitude": lat,
        "longitude": lon,
        "altitude_m": altitude,
        "fix_quality": fix_quality,
        "num_sats": num_sats,
        "hdop": hdop,
        "gps_time_utc": fields[1] or "",
    }


def parse_rmc(fields: list[str]) -> Optional[dict]:
    """
    Parse RMC sentence fields.

    Example:
    $GPRMC,time,status,lat,NS,lon,EW,speed,course,date,...
    """
    if len(fields) < 10:
        return None

    status = fields[2]
    if status != "A":  # A = valid, V = void
        return None

    lat = nmea_to_decimal(fields[3], fields[4])
    lon = nmea_to_decimal(fields[5], fields[6])

    if lat is None or lon is None:
        return None

    return {
        "source": "RMC",
        "latitude": lat,
        "longitude": lon,
        "altitude_m": "",
        "fix_quality": "",
        "num_sats": "",
        "hdop": "",
        "gps_time_utc": fields[1] or "",
        "gps_date": fields[9] or "",
    }


def verify_nmea_checksum(sentence: str) -> bool:
    """
    Verify NMEA checksum. Returns True if valid or if no checksum present.
    """
    sentence = sentence.strip()
    if not sentence.startswith("$"):
        return False

    if "*" not in sentence:
        return True

    body, checksum_text = sentence[1:].split("*", 1)
    checksum_text = checksum_text[:2]

    try:
        expected = int(checksum_text, 16)
    except ValueError:
        return False

    actual = 0
    for ch in body:
        actual ^= ord(ch)

    return actual == expected


def parse_nmea_sentence(sentence: str) -> Optional[dict]:
    sentence = sentence.strip()

    if not sentence.startswith("$"):
        return None

    if not verify_nmea_checksum(sentence):
        return None

    # Strip leading $ and trailing checksum
    body = sentence[1:].split("*", 1)[0]
    fields = body.split(",")

    if not fields:
        return None

    msg_type = fields[0]

    if msg_type.endswith("GGA"):
        return parse_gga(fields)
    if msg_type.endswith("RMC"):
        return parse_rmc(fields)

    return None


def ensure_csv_header(path: Path) -> None:
    file_exists = path.exists()
    if not file_exists or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "logged_at_utc",
                    "source",
                    "latitude",
                    "longitude",
                    "altitude_m",
                    "fix_quality",
                    "num_sats",
                    "hdop",
                    "gps_time_utc",
                    "gps_date",
                    "raw_sentence",
                ]
            )


def open_serial(port: str, baudrate: int, timeout: float) -> serial.Serial:
    return serial.Serial(
        port=port,
        baudrate=baudrate,
        timeout=timeout,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Log GPS coordinates from USB serial to CSV.")
    parser.add_argument("--port", required=True, help="Serial port, e.g. COM3 or /dev/ttyACM0")
    parser.add_argument("--baudrate", type=int, default=9600, help="Serial baudrate (default: 9600)")
    parser.add_argument("--output", default="gps_log.csv", help="Output CSV filename")
    parser.add_argument("--timeout", type=float, default=1.0, help="Serial read timeout in seconds")
    args = parser.parse_args()

    output_path = Path(args.output)
    ensure_csv_header(output_path)

    try:
        ser = open_serial(args.port, args.baudrate, args.timeout)
    except serial.SerialException as e:
        print(f"Failed to open serial port {args.port}: {e}", file=sys.stderr)
        return 1

    print(f"Logging GPS data from {args.port} to {output_path}")
    print("Press Ctrl+C to stop.")

    try:
        with ser, output_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            while True:
                try:
                    line = ser.readline()
                except serial.SerialException as e:
                    print(f"Serial read error: {e}", file=sys.stderr)
                    return 1

                if not line:
                    continue

                try:
                    sentence = line.decode("ascii", errors="replace").strip()
                except Exception:
                    continue

                parsed = parse_nmea_sentence(sentence)
                if not parsed:
                    continue

                logged_at = datetime.now(timezone.utc).isoformat()

                row = [
                    logged_at,
                    parsed.get("source", ""),
                    parsed.get("latitude", ""),
                    parsed.get("longitude", ""),
                    parsed.get("altitude_m", ""),
                    parsed.get("fix_quality", ""),
                    parsed.get("num_sats", ""),
                    parsed.get("hdop", ""),
                    parsed.get("gps_time_utc", ""),
                    parsed.get("gps_date", ""),
                    sentence,
                ]

                writer.writerow(row)
                f.flush()

                print(
                    f"{logged_at}  "
                    f"lat={parsed.get('latitude')}  "
                    f"lon={parsed.get('longitude')}  "
                    f"alt={parsed.get('altitude_m', '')}"
                )

        return 0

    except KeyboardInterrupt:
        print("\nStopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())