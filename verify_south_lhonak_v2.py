import ee

ee.Initialize(project='draft-glacier')

point = ee.Geometry.Point([88.2797242, 27.9442492])
years = range(2016, 2025)

print("=== South Lhonak, Google Earth coordinates ===")
for year in years:
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point)
        .filterDate(f'{year}-01-01', f'{year}-12-31')
        .filterMetadata('CLOUD_COVER', 'less_than', 50)
        .sort('CLOUD_COVER'))
    count = collection.size().getInfo()
    if count == 0:
        print(f"{year}: no image")
        continue
    image = collection.first()
    ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
    water = ndwi.gt(0.2)
    area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=point.buffer(1500), scale=30, maxPixels=1e9
    ).getInfo().get('NDWI')
    print(f"{year}: {area} m2")
