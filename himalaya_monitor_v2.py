import ee
import csv
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

rows = []

for name, info in sites.items():
    print("Processing " + name + "...")
    lake_raw = {}
    snow_raw = {}
    snow_counts = {}

    for year in years:
        lake_raw[year] = get_lake_area(info['point'], info['buffer'], year)
        snow_val, snow_n = get_snow_cover(info['point'], info['buffer'], year)
        snow_raw[year] = snow_val
        snow_counts[year] = snow_n

    # --- Lake contamination flagging (median-based, same logic as risk_scored_lakes_v3) ---
    valid_lake_vals = sorted([v for v in lake_raw.values() if v is not None and v > 0])
    lake_median_all = valid_lake_vals[len(valid_lake_vals)//2] if valid_lake_vals else None

    # --- Snow anomaly baseline (mean/std across valid years) ---
    valid_snow_vals = [v for v in snow_raw.values() if v is not None]
    snow_mean = sum(valid_snow_vals)/len(valid_snow_vals) if valid_snow_vals else None
    snow_std = (sum((v-snow_mean)**2 for v in valid_snow_vals)/len(valid_snow_vals))**0.5 if valid_snow_vals else None

    for year in years:
        lake_val = lake_raw[year]
        lake_flag = ""
        if lake_val is None:
            lake_flag = "no_image"
        elif lake_median_all and lake_val < 0.1 * lake_median_all:
            lake_flag = "contaminated"
        else:
            lake_flag = "ok"

        snow_val = snow_raw[year]
        snow_flag = ""
        if snow_val is None:
            snow_flag = "no_image"
        elif snow_std and snow_std > 0 and snow_val < (snow_mean - 1.0*snow_std):
            snow_flag = "low_snow_anomaly"
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

with open('himalaya_monitor_data_v2.csv', 'w', newline='') as f:
    fieldnames = ['site','year','dam_type','lake_area_m2','lake_status',
                  'snow_cover_index','snow_images_used','snow_status','last_updated']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Done. Data saved to himalaya_monitor_data_v2.csv")
