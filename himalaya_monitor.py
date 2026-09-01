import ee
import csv
from datetime import datetime

ee.Initialize(project='draft-glacier')

# Your existing 10 lakes, expandable later
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

def get_snow_anomaly(point, buffer_m, year):
    collection = (ee.ImageCollection('MODIS/061/MOD10A1')
        .filterBounds(point.buffer(buffer_m))
        .filterDate(str(year)+'-06-01', str(year)+'-08-31'))
    if collection.size().getInfo() == 0:
        return None
    mean_img = collection.select('NDSI_Snow_Cover').mean()
    val = mean_img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point.buffer(buffer_m), scale=500, maxPixels=1e9
    ).getInfo().get('NDSI_Snow_Cover')
    return val

years = range(2016, 2025)
rows = []

for name, info in sites.items():
    print("Processing " + name + "...")
    lake_areas = {}
    snow_vals = {}
    for year in years:
        lake_areas[year] = get_lake_area(info['point'], info['buffer'], year)
        snow_vals[year] = get_snow_anomaly(info['point'], info['buffer'], year)

    valid_lake = sorted([v for v in lake_areas.values() if v and v > 0])
    valid_snow = [v for v in snow_vals.values() if v is not None]

    lake_median = valid_lake[len(valid_lake)//2] if valid_lake else None
    snow_mean = sum(valid_snow)/len(valid_snow) if valid_snow else None

    for year in years:
        rows.append({
            'site': name,
            'year': year,
            'dam_type': info['dam_type'],
            'lake_area_m2': lake_areas[year],
            'snow_cover_index': snow_vals[year],
            'last_updated': datetime.now().isoformat()
        })

with open('himalaya_monitor_data.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['site','year','dam_type','lake_area_m2','snow_cover_index','last_updated'])
    writer.writeheader()
    writer.writerows(rows)

print("Done. Data saved to himalaya_monitor_data.csv")
