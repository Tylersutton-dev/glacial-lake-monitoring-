import ee

ee.Initialize(project='draft-glacier')

point = ee.Geometry.Point([88.2797242, 27.9442492])

# Restrict to peak summer only (Aug), when ice cover is most likely minimal at high elevation
for year in range(2016, 2023):  # stop before the 2023 collapse for now
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point)
        .filterDate(f'{year}-08-01', f'{year}-08-31')
        .filterMetadata('CLOUD_COVER', 'less_than', 60)
        .sort('CLOUD_COVER'))
    count = collection.size().getInfo()
    if count == 0:
        print(f"{year}: no August image")
        continue
    image = collection.first()
    ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
    # Try a lower threshold too, in case partial ice mix is suppressing the signal
    water_loose = ndwi.gt(0.0)
    area = water_loose.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=point.buffer(1500), scale=30, maxPixels=1e9
    ).getInfo().get('NDWI')
    print(f"{year} (August, loose threshold): {area} m2")
