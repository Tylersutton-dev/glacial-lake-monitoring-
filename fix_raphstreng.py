import ee

ee.Initialize(project='draft-glacier')

point = ee.Geometry.Point([90.2460886, 28.1058503])
buffer_m = 1000

years = range(2016, 2025)

print("=== Raphstreng Tsho, corrected coordinates ===")
for year in years:
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point)
        .filterDate(str(year)+'-01-01', str(year)+'-12-31')
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
        reducer=ee.Reducer.sum(), geometry=point.buffer(buffer_m), scale=30, maxPixels=1e9
    ).getInfo().get('NDWI')
    print(f"{year}: {area} m2")
