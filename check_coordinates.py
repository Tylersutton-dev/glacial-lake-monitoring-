import re
import glob

# Matches ee.Geometry.Point([lon, lat]) calls
pattern = re.compile(r'ee\.Geometry\.Point\(\[\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*\]\)')

print("Scanning all .py files for coordinate points...\n")
print(f"{'File':<35} {'Longitude':<15} {'Latitude':<15} {'Flag'}")
print("-" * 80)

suspicious_count = 0
total_count = 0

for filepath in glob.glob('*.py'):
    with open(filepath) as f:
        content = f.read()
    for match in pattern.finditer(content):
        lon, lat = match.group(1), match.group(2)
        total_count += 1
        # Flag anything that's suspiciously round: whole numbers or one decimal only
        lon_decimals = len(lon.split('.')[1]) if '.' in lon else 0
        lat_decimals = len(lat.split('.')[1]) if '.' in lat else 0
        is_suspicious = lon_decimals <= 1 and lat_decimals <= 1
        flag = "  <-- SUSPICIOUS (too round)" if is_suspicious else ""
        if is_suspicious:
            suspicious_count += 1
        print(f"{filepath:<35} {lon:<15} {lat:<15} {flag}")

print("-" * 80)
print(f"\nTotal coordinates found: {total_count}")
print(f"Suspiciously round coordinates: {suspicious_count}")
