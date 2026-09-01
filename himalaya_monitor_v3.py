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

years = range(2016, 2025)

def get_lake_area_median(point, buffer_m, year):
    # Pull ALL reasonably-clear images for the year, not just the single least-cloudy one
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point)
        .filterDate(str(year)+'-01-01', str(year)+'-12-31')
        .filterMetadata('CLOUD_COVER', 'less_than', 50)
        .sort('CLOUD_COVER'))

    count = collection.size().getInfo()
    if count == 0:
        return None, 0

    n_images = min(count, 6)  # up to 6 images, same spirit as your snow multi-image fix
    images = collection.limit(n_images).toList(n_images)

    areas = []
    for i in range(n_images):
        img = ee.Image(images.get(i))
        ndwi = img.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
        water = ndwi.gt(0.2)
        area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=point.buffer(buffer_m), scale=30, maxPixels=1e9
        ).getInfo().get('NDWI')
        if area is not None and area > 0:
            areas.append(area)

    if not areas:
        return None, 0

    areas.sort()
    median_area = areas[len(areas)//2]
    return median_area, len(areas)

print("=== Rebuilding lake data with multi-image median (fixing contamination) ===")
rows = []

for name, info in sites.items():
    print("Processing " + name + "...")
    lake_results = {}
    for year in years:
        val, n = get_lake_area_median(info['point'], info['buffer'], year)
        lake_results[year] = (val, n)

    valid = sorted([v[0] for v in lake_results.values() if v[0] is not None])
    site_median = valid[len(valid)//2] if valid else None

    for year in years:
        val, n = lake_results[year]
        if val is None:
            status = "no_image"
        elif site_median and val < 0.1 * site_median:
            status = "contaminated"
        else:
            status = "ok"

        rows.append({
            'site': name, 'year': year, 'dam_type': info['dam_type'],
            'lake_area_m2': val if val is not None else '',
            'lake_status': status,
            'images_used': n,
            'last_updated': datetime.now().isoformat()
        })

with open('himalaya_lakes_v3.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['site','year','dam_type','lake_area_m2','lake_status','images_used','last_updated'])
    writer.writeheader()
    writer.writerows(rows)

print("Done. Data saved to himalaya_lakes_v3.csv")
