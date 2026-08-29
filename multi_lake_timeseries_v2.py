import ee

ee.Initialize(project='draft-glacier')

# Each lake gets its own point AND its own buffer size,
# roughly matched to its real documented size, not one-size-fits-all.
lakes = {
    'Tsho Rolpa': {'point': ee.Geometry.Point([86.467, 27.867]), 'buffer': 2000},
    'Imja Tsho': {'point': ee.Geometry.Point([86.928, 27.898]), 'buffer': 1500},
    'Thulagi': {'point': ee.Geometry.Point([84.5403, 28.5208]), 'buffer': 600}
}

years = range(2014, 2025)

def get_area(lake_point, buffer_m, start, end):
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(lake_point)
        .filterDate(start, end)
        .sort('CLOUD_COVER'))

    count = collection.size().getInfo()
    if count == 0:
        return None

    image = collection.first()
    ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
    water = ndwi.gt(0.2)

    area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=lake_point.buffer(buffer_m),
        scale=30
    )
    result = area.getInfo()
    return result.get('NDWI')

for name, info in lakes.items():
    print("=== " + name + " ===")

    raw_results = {}
    for year in years:
        start = str(year) + '-01-01'
        end = str(year) + '-12-31'
        val = get_area(info['point'], info['buffer'], start, end)
        raw_results[year] = val

    # Compute median of valid (non-None) readings to use as a sanity baseline
    valid_vals = [v for v in raw_results.values() if v is not None and v > 0]
    valid_vals.sort()
    if len(valid_vals) > 0:
        median = valid_vals[len(valid_vals) // 2]
    else:
        median = None

    print("Year, Area (sq m), Status")
    for year in years:
        val = raw_results[year]
        if val is None:
            print(str(year) + ", n/a, no image available")
        elif median is not None and val < 0.1 * median:
            print(str(year) + ", " + str(val) + ", FLAGGED as likely cloud/snow contamination")
        else:
            print(str(year) + ", " + str(val) + ", ok")

    print("")
