import ee

ee.Initialize(project='draft-glacier')

lake = ee.Geometry.Point([86.47, 27.85])
years = range(2014, 2025)

print("Year, Lake area (sq meters)")

for year in years:
    start = str(year) + '-01-01'
    end = str(year) + '-12-31'

    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(lake)
        .filterDate(start, end)
        .sort('CLOUD_COVER'))

    count = collection.size().getInfo()

    if count == 0:
        print(str(year) + ", no clear image available")
        continue

    image = collection.first()

    ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
    water = ndwi.gt(0.2)

    area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=lake.buffer(2000),
        scale=30
    )

    result = area.getInfo()
    print(str(year) + ", " + str(result.get('NDWI')))
