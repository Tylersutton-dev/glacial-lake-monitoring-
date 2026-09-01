import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

collection = (ee.ImageCollection('MODIS/061/MOD10A1')  # daily snow cover product
    .filterBounds(region)
    .filterDate('2017-06-01', '2017-08-31'))

count = collection.size().getInfo()
print("MODIS daily snow images found for summer 2017: " + str(count))

if count > 0:
    ndsi_snow_cover = collection.select('NDSI_Snow_Cover').mean()
    result = ndsi_snow_cover.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=500, maxPixels=1e9)
    print("Mean summer 2017 NDSI Snow Cover: " + str(result.getInfo()))
