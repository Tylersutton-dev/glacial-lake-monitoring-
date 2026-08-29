import ee

ee.Initialize(project='draft-glacier')

lake = ee.Geometry.Point([86.47, 27.85])

image = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(lake)
    .filterDate('2020-01-01', '2020-12-31')
    .sort('CLOUD_COVER')
    .first())

ndwi = image.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
water = ndwi.gt(0.2)

area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
    reducer=ee.Reducer.sum(),
    geometry=lake.buffer(2000),
    scale=30
)

print(area.getInfo())
