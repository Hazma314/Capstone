pip install simplekml pyproj shapely 
import gps
import time
import csv
from shapely.geometry import Polygon, LineString
#import gps
#import csv
import math
from geopy.distance import geodesic
#import gps
#import time
import simplekml
from shapely.geometry import Polygon
from pyproj import Geod

# Connect to GPS
session = gps.gps("localhost", "2947")
session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

recorded_points = []

print("--- Area Recorder Started ---")
print("Walk the perimeter. Press Ctrl+C when finished.")

try:
    while True:
        report = session.next()
        if report['class'] == 'TPV':
            lat = getattr(report, 'lat', 0.0)
            lon = getattr(report, 'lon', 0.0)
            
            if lat and lon:
                # Store as (longitude, latitude) for KML/Shapely compatibility
                point = (lon, lat)
                
                # Only record if we've moved significantly or every few seconds
                if not recorded_points or point != recorded_points[-1]:
                    recorded_points.append(point)
                    print(f"Recorded point {len(recorded_points)}: {lat}, {lon}", end='\r')
                
        time.sleep(1)

except KeyboardInterrupt:
    if len(recorded_points) < 3:
        print("\nError: Need at least 3 points to define an area.")
    else:
        print(f"\nProcessing {len(recorded_points)} points...")

        # 1. Calculate the actual area in square meters
        # Uses WGS84 ellipsoid for high accuracy
        geod = Geod(ellps="WGS84")
        poly_geom = Polygon(recorded_points)
        area, perimeter = geod.geometry_area_perimeter(poly_geom)
        
        # 2. Save as KML Polygon
        kml = simplekml.Kml()
        # Points must be (lon, lat)
        pol = kml.newpolygon(name="Recorded Area", 
                             outerboundaryis=recorded_points)
        pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.green)
        
        kml.save("recorded_area.kml") #input from user instead
        
        print(f"Success! File saved as 'recorded_area.kml'")
        print(f"Total Area: {abs(area):.2f} square meters") #change to acrege
        print(f"Perimeter: {perimeter:.2f} meters")

#--------------------------------------------------------------------------------------------------------------
# Configuration
SPACING_METERS = 2.0  # Distance between each parallel path line (swath width)

def generate_coverage_path(points, spacing):
    """Generates a zig-zag path to cover the polygon area."""
    poly = Polygon(points)
    minx, miny, maxx, maxy = poly.bounds
    
    # Convert meters to approximate degrees (0.00001 deg approx 1.1m)
    deg_spacing = spacing / 111320.0 
    
    path = []
    current_y = miny
    reverse = False
    
    while current_y < maxy:
        # Create a horizontal line across the bounding box
        line = LineString([(minx, current_y), (maxx, current_y)])
        # Intersect line with our recorded area
        intersection = line.intersection(poly)
        
        if not intersection.is_empty:
            # Handle cases where the line might be split by the polygon shape
            if intersection.geom_type == 'LineString':
                coords = list(intersection.coords)
                if reverse: coords.reverse()
                path.extend(coords)
                reverse = not reverse # Zig-zag pattern
        
        current_y += deg_spacing
    return path

# --- Recording Phase ---
#session = gps.gps("localhost", "2947")
#session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
#recorded_points = []

#print("1. WALK THE PERIMETER. Press Ctrl+C when done.")
#try:
 #   while True:
  #      report = session.next()
   #     if report['class'] == 'TPV':
    #        lat, lon = getattr(report, 'lat', 0.0), getattr(report, 'lon', 0.0)
     #       if lat and lon:
      #          if not recorded_points or (lon, lat) != recorded_points[-1]:
       #             recorded_points.append((lon, lat))
        #            print(f"Points: {len(recorded_points)}", end='\r')
        #time.sleep(0.5)
#except KeyboardInterrupt:
#    print("\nRecording Finished.")

# --- Path Generation Phase ---
if len(recorded_points) >= 3:
    print(f"2. GENERATING COVERAGE PATH (Spacing: {SPACING_METERS}m)...")
    coverage_path = generate_coverage_path(recorded_points, SPACING_METERS)
    
    # Save to CSV for the "Follow Path" script
    # Might need to adjust to tie into waypoints
    with open('coverage_path.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['lat', 'lon'])
        for lon, lat in coverage_path:
            writer.writerow([lat, lon])
            
    print(f"Success! {len(coverage_path)} waypoints saved to 'coverage_path.csv'.")
else:
    print("Error: Not enough points to form an area.")
#-------------------------------------------------------------------------------------------------------------------------------

# Following path
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
#session = gps.gps("localhost", "2947")
#session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)

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
#-----------------------------------------------------------------------------------------------------------------------------
