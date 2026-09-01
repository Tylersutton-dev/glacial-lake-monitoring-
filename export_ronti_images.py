import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000).bounds()  # 3km box around the collapse site

# Pull one clear image per year, summer months only (less snow interference)
years = range(2016, 2021)  # covers pre-collapse period through the Feb 2021 event

for year in years:
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(ronti_peak)
        .filterDate(str(year) + '-06-01', str(year) + '-09-30')
        .sort('CLOUDY_PIXEL_PERCENTAGE'))

    count = collection.size().getInfo()
    if count == 0:
        print(str(year) + ": no clear image found")
        continue

    image = collection.first().select(['B4', 'B3', 'B2'])  # true color bands

    task = ee.batch.Export.image.toDrive(
        image=image,
        description='ronti_peak_' + str(year),
        folder='glacier_avalanche_export',
        region=region,
        scale=10,
        maxPixels=1e9
    )
    task.start()
    print(str(year) + ": export started (task id " + task.id + ")")

print("All export tasks submitted. Check https://code.earthengine.google.com/tasks for progress.")
