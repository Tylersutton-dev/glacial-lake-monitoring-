import csv

INPUT_FILE = 'himalaya_monitor_data_v2.csv'
OUTPUT_FILE = 'himalaya_monitor_data_v7_scoped.csv'

# Sites excluded due to confirmed high-elevation ice-cover detection failure
EXCLUDED_SITES = ['South Lhonak']

with open(INPUT_FILE) as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = [r for r in reader if r['site'].strip() not in EXCLUDED_SITES]

with open(OUTPUT_FILE, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Removed {len(EXCLUDED_SITES)} site(s): {EXCLUDED_SITES}")
print(f"Remaining rows: {len(rows)}")
