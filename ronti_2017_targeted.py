import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

# Widen the window even further: April through November,
# and loosen the cloud filter slightly, specifically to rescue 2017's weak sample size
collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(region)
    .filterDate('2017-04-01', '2017-11-30')
    .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 40)
    .sort('CLOUDY_PIXEL_PERCENTAGE'))

count = collection.size().getInfo()
print("Total usable images found for 2017 (Apr-Nov, <40% cloud): " + str(count))

if count == 0:
    print("Still no images found, even with widened window.")
else:
    n_images = min(count, 10)  # take up to 10 this time, not just 5
    images = collection.limit(n_images).toList(n_images)

    print("Year, Date, NDSI, Cloud%")
    ndsi_values = []
    for i in range(n_images):
        img = ee.Image(images.get(i))
        date = img.date().format('YYYY-MM-dd').getInfo()
        cloud_pct = img.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        ndsi = img.normalizedDifference(['B3', 'B11']).rename('NDSI')
        mean_val = ndsi.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=region, scale=20, maxPixels=1e9
        ).getInfo().get('NDSI')

        if mean_val is not None:
            ndsi_values.append(mean_val)
            print("2017, " + date + ", " + str(round(mean_val, 4)) + ", " + str(round(cloud_pct, 1)) + "%")

    if ndsi_values:
        avg = sum(ndsi_values) / len(ndsi_values)
        print("")
        print("2017 average NDSI across " + str(len(ndsi_values)) + " images: " + str(round(avg, 4)))
    else:
        print("No valid NDSI readings extracted.")
