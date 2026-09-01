import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000).bounds()

years = [2016, 2017]

for year in years:
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(ronti_peak)
        .filterDate(str(year) + '-06-01', str(year) + '-09-30')
        .sort('CLOUDY_PIXEL_PERCENTAGE'))

    count = collection.size().getInfo()
    if count == 0:
        print(str(year) + ": no clear image found")
        continue

    image = collection.first().select(['B4', 'B3', 'B2'])

    task = ee.batch.Export.image.toDrive(
        image=image,
        description='ronti_peak_' + str(year) + '_v2',
        folder='glacier_avalanche_export_v2',
        region=region,
        scale=10,
        maxPixels=1e9
    )
    task.start()
    print(str(year) + ": export started (task id " + task.id + ")")

print("Done. Check https://code.earthengine.google.com/tasks for progress.")
