import ee

ee.Initialize(project='draft-glacier')

point = ee.Geometry.Point([88.2797242, 27.9442492])
region = point.buffer(3000).bounds()

# Use a pre-collapse year so the lake should be at its largest and most visible
collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
    .filterBounds(point)
    .filterDate('2022-01-01', '2022-12-31')
    .filterMetadata('CLOUD_COVER', 'less_than', 30)
    .sort('CLOUD_COVER'))

image = collection.first()

task = ee.batch.Export.image.toDrive(
    image=image.select(['SR_B4', 'SR_B3', 'SR_B2']),
    description='south_lhonak_check_2022',
    folder='glacier_avalanche_export_v2',
    region=region,
    scale=30,
    maxPixels=1e9
)
task.start()
print("Export started, check https://code.earthengine.google.com/tasks")
