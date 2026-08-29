import ee

ee.Initialize(project='draft-glacier')

lake = ee.Geometry.Point([84.5403, 28.5208])
buffer_m = 600
years = range(2016, 2025)  # Sentinel-2 archive starts mid-2015

print("=== Thulagi (Sentinel-2, 10m resolution) ===")
print("Year, Area (sq m), Status")

results = {}
for year in years:
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'

    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(lake)
        .filterDate(start, end)
        .sort('CLOUDY_PIXEL_PERCENTAGE'))

    count = collection.size().getInfo()
    if count == 0:
        results[year] = None
        continue

    image = collection.first()
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
    water = ndwi.gt(0.2)

    area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=lake.buffer(buffer_m),
        scale=10,  # matches Sentinel-2's native resolution
        maxPixels=1e9
    )
    results[year] = area.getInfo().get('NDWI')

valid_vals = sorted([v for v in results.values() if v is not None and v > 0])
median = valid_vals[len(valid_vals)//2] if valid_vals else None

for year in years:
    val = results[year]
    if val is None:
        print(str(year) + ", n/a, no image available")
    elif median is not None and val < 0.1 * median:
        print(str(year) + ", " + str(val) + ", FLAGGED as likely contamination")
    else:
        print(str(year) + ", " + str(val) + ", ok")
