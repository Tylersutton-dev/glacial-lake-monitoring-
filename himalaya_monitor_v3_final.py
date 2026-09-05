import ee
import csv
import random
from datetime import datetime

ee.Initialize(project='draft-glacier')

sites = {
    'Lower Barun':  {'point': ee.Geometry.Point([87.092, 27.798]), 'buffer': 1000, 'dam_type': 'moraine'},
    'Chamlang':     {'point': ee.Geometry.Point([86.958, 27.755]), 'buffer': 800,  'dam_type': 'moraine'},
    'Hongu 2':      {'point': ee.Geometry.Point([86.957, 27.783]), 'buffer': 800,  'dam_type': 'moraine'},
    'Hongu 1':      {'point': ee.Geometry.Point([86.935, 27.838]), 'buffer': 800,  'dam_type': 'moraine'},
    'Imja Tsho':    {'point': ee.Geometry.Point([86.925, 27.898]), 'buffer': 1500, 'dam_type': 'moraine'},
    'Lumding':      {'point': ee.Geometry.Point([86.612, 27.779]), 'buffer': 1000, 'dam_type': 'moraine'},
    'Tsho Rolpa':   {'point': ee.Geometry.Point([86.476, 27.861]), 'buffer': 2000, 'dam_type': 'moraine'},
    'Ronti Peak':   {'point': ee.Geometry.Point([79.719, 30.369]), 'buffer': 3000, 'dam_type': 'slope'},
    # FIXED: was [84.516, 28.738], a mis-transcribed latitude (~24km off).
    # Verified against this project's own earlier standalone testing of Thulagi Tsho.
    'Thulagi Tsho':  {'point': ee.Geometry.Point([84.5403, 28.5208]), 'buffer': 1500, 'dam_type': 'moraine'},
    # FIXED: was [89.950, 28.050], had been a rough approximation.
    # Real coordinate verified via Google Earth + cross-referenced against Lunana-region
    # sources (Lugge Tsho, adjacent to Raphstreng, sits at ~90.29, 28.09).
    'Raphstreng Tsho': {'point': ee.Geometry.Point([90.2460886, 28.1058503]), 'buffer': 1000, 'dam_type': 'moraine'},
    # South Lhonak REMOVED: confirmed via Google Earth coordinates (27.9442492, 88.2797242)
    # that this is the correct location, but at 5200m the lake stays partially ice-covered
    # even in summer, defeating standard NDWI regardless of coordinate accuracy.
    # Documented scope boundary: this dataset covers lakes up to ~4800-5000m.
}

# Add five reproducibly selected lake candidates detected by Earth Engine.
random.seed(42)
try:
    with open("discovered_lakes.csv", newline="") as file:
        discovered_lakes = list(csv.DictReader(file))
except FileNotFoundError:
    discovered_lakes = []

lake_candidates = random.sample(discovered_lakes, min(5, len(discovered_lakes)))
for candidate in lake_candidates:
    sites["Candidate Lake " + candidate["candidate_id"]] = {
        "point": ee.Geometry.Point([
            float(candidate["lon"]),
            float(candidate["lat"])
        ]),
        "buffer": 1000,
        "dam_type": "candidate_moraine"
    }

# Add five reproducibly selected high-elevation mountain candidates.
mountain_region = ee.Geometry.Rectangle([86.6, 27.6, 87.2, 28.1])
mountain_points = ee.FeatureCollection.randomPoints(
    region=mountain_region,
    points=100,
    seed=42,
    maxError=100
)

dem = ee.Image("USGS/SRTMGL1_003").rename("elevation")
mountain_points = mountain_points.map(
    lambda feature: feature.set(
        "elevation",
        dem.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=feature.geometry(),
            scale=30,
            maxPixels=1000
        ).get("elevation")
    )
)
high_mountain_points = mountain_points.filter(ee.Filter.gte("elevation", 4500))

mountain_features = high_mountain_points.limit(5).getInfo()["features"]
for index, feature in enumerate(mountain_features, start=1):
    coordinates = feature["geometry"]["coordinates"]
    sites["Candidate Mountain " + str(index)] = {
        "point": ee.Geometry.Point(coordinates),
        "buffer": 3000,
        "dam_type": "candidate_slope"
    }

DAM_RISK_WEIGHT = {'moraine': 1.5, 'ice': 1.2, 'bedrock': 0.5, 'slope': 1.0, 'unknown': 1.0}
years = range(2016, 2025)

def get_lake_area(point, buffer_m, year):
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point).filterDate(str(year)+'-01-01', str(year)+'-12-31')
        .sort('CLOUD_COVER'))
    if collection.size().getInfo() == 0:
        return None
    image = collection.first()
    ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
    water = ndwi.gt(0.2)
    area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=point.buffer(buffer_m), scale=30, maxPixels=1e9)
    return area.getInfo().get('NDWI')

def get_snow_cover(point, buffer_m, year):
    collection = (ee.ImageCollection('MODIS/061/MOD10A1')
        .filterBounds(point.buffer(buffer_m))
        .filterDate(str(year)+'-06-01', str(year)+'-08-31'))
    if collection.size().getInfo() == 0:
        return None, 0
    mean_img = collection.select('NDSI_Snow_Cover').mean()
    val = mean_img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(buffer_m), scale=500, maxPixels=1e9
    ).getInfo().get('NDSI_Snow_Cover')
    return val, collection.size().getInfo()

# --- IMPROVED anomaly logic ---
# Motivated by a control-group finding: random high-elevation "mountain control"
# points showed a HIGHER single-year anomaly rate (17.8%) than named risk lakes
# (11.1%), meaning a simple per-site 1-std-dev-below-mean flag was mostly catching
# ordinary noise, not real signal. This version requires BOTH a statistically
# meaningful dip (>1 std dev below the site's own mean) AND a meaningful magnitude
# drop (>20% below mean) AND that the dip holds for 2+ consecutive years, since a
# real destabilization is expected to persist, not appear for one isolated year.
def compute_confirmed_anomalies(values_by_year, mean_val, std_val):
    years_sorted = sorted(values_by_year.keys())
    raw_flags = {}
    for year in years_sorted:
        val = values_by_year[year]
        if val is None or mean_val is None:
            raw_flags[year] = False
            continue
        stat_anomaly = std_val is not None and std_val > 0 and val < (mean_val - 1.0 * std_val)
        magnitude_anomaly = val < mean_val * 0.8
        raw_flags[year] = stat_anomaly and magnitude_anomaly

    confirmed = {y: False for y in years_sorted}
    for i in range(1, len(years_sorted)):
        y_prev, y_curr = years_sorted[i-1], years_sorted[i]
        if raw_flags[y_prev] and raw_flags[y_curr]:
            confirmed[y_prev] = True
            confirmed[y_curr] = True
    return confirmed

rows = []

for name, info in sites.items():
    print("Processing " + name + "...")
    lake_raw = {}
    snow_raw = {}
    snow_counts = {}

    is_slope_site = info['dam_type'] in ('slope', 'candidate_slope')

    for year in years:
        lake_raw[year] = None if is_slope_site else get_lake_area(
            info['point'], info['buffer'], year
        )
        snow_val, snow_n = get_snow_cover(info['point'], info['buffer'], year)
        snow_raw[year] = snow_val
        snow_counts[year] = snow_n

    valid_lake_vals = sorted([v for v in lake_raw.values() if v is not None and v > 0])
    lake_median_all = valid_lake_vals[len(valid_lake_vals)//2] if valid_lake_vals else None

    valid_snow_vals = [v for v in snow_raw.values() if v is not None]
    snow_mean = sum(valid_snow_vals)/len(valid_snow_vals) if valid_snow_vals else None
    snow_std = (sum((v-snow_mean)**2 for v in valid_snow_vals)/len(valid_snow_vals))**0.5 if valid_snow_vals else None

    confirmed_anomalies = compute_confirmed_anomalies(snow_raw, snow_mean, snow_std)

    for year in years:
        lake_val = lake_raw[year]
        if is_slope_site:
            lake_flag = "not_applicable"
        elif lake_val is None:
            lake_flag = "no_image"
        elif lake_median_all is None:
            lake_flag = "no_valid_baseline"
        elif lake_val == 0 or lake_val < 0.1 * lake_median_all:
            lake_flag = "contaminated"
        else:
            lake_flag = "ok"

        snow_val = snow_raw[year]
        if snow_val is None:
            snow_flag = "no_image"
        elif confirmed_anomalies.get(year):
            snow_flag = "confirmed_low_snow_anomaly"
        elif snow_std and snow_std > 0 and snow_val < (snow_mean - 1.0*snow_std):
            snow_flag = "single_year_dip"  # statistically low but not confirmed persistent
        else:
            snow_flag = "normal"

        rows.append({
            'site': name,
            'year': year,
            'dam_type': info['dam_type'],
            'lake_area_m2': lake_val if lake_val is not None else '',
            'lake_status': lake_flag,
            'snow_cover_index': round(snow_val, 3) if snow_val is not None else '',
            'snow_images_used': snow_counts[year],
            'snow_status': snow_flag,
            'last_updated': datetime.now().isoformat()
        })

with open('himalaya_monitor_data_v3.csv', 'w', newline='') as f:
    fieldnames = ['site','year','dam_type','lake_area_m2','lake_status',
                  'snow_cover_index','snow_images_used','snow_status','last_updated']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Done. Data saved to himalaya_monitor_data_v3.csv")
