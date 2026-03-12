import gps
import csv
import math
from geopy.distance import geodesic

# Configuration
PATH_FILE = 'coverage_path.csv'
ARRIVAL_RADIUS = 3.0  # Meters before switching to next point

def get_bearing(lat1, lon1, lat2, lon2):
    """Calculates the bearing between two points for navigation."""
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    y = math.sin(d_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - \
        math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# 1. Load the generated path
waypoints = []
try:
    with open(PATH_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        waypoints = [(float(row['lat']), float(row['lon'])) for row in reader]
    print(f"Loaded {len(waypoints)} waypoints.")
except FileNotFoundError:
    print(f"Error: {PATH_FILE} not found. Run the recording script first.")
    exit()

# 2. Initialize GPS connection
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

current_idx = 0

print("--- Navigation Started ---")
try:
    while current_idx < len(waypoints):
        report = session.next()
        
        # Look for Time Position Velocity (TPV) reports
        if report['class'] == 'TPV':
            curr_lat = getattr(report, 'lat', 0.0)
            curr_lon = getattr(report, 'lon', 0.0)
            
            if curr_lat and curr_lon:
                target = waypoints[current_idx]
                dist = geodesic((curr_lat, curr_lon), target).meters
                bearing = get_bearing(curr_lat, curr_lon, target[0], target[1])
                
                print(f"WP {current_idx+1}/{len(waypoints)} | Dist: {dist:.1f}m | Heading: {bearing:.1f}Â°", end='\r')
                
                # Check for arrival at waypoint
                if dist <= ARRIVAL_RADIUS:
                    print(f"\n[!] Reached Waypoint {current_idx + 1}")
                    current_idx += 1
                    if current_idx < len(waypoints):
                        print(f"Targeting Next Point: {waypoints[current_idx]}")

    print("\nMission Complete: Area covered successfully!")

except KeyboardInterrupt:
    print("\nNavigation halted by user.")