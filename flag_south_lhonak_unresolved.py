import csv
from datetime import datetime

INPUT_FILE = 'himalaya_monitor_data_v2.csv'
OUTPUT_FILE = 'himalaya_monitor_data_v6_flagged.csv'

with open(INPUT_FILE) as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

updated = 0
for row in rows:
    if row['site'].strip() == 'South Lhonak':
        row['lake_area_m2'] = ''
        row['lake_status'] = 'detection_unresolved'
        row['last_updated'] = datetime.now().isoformat()
        updated += 1

with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Marked {updated} South Lhonak rows as detection_unresolved")
