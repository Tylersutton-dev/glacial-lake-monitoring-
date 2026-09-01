import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

years = range(2016, 2021)  # matches your image export window, pre-collapse period

def get_summer_ndsi(point_region, year):
    # Focus on peak summer melt season (July-August), when Yang et al. found the anomaly
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(point_region)
        .filterDate(str(year) + '-07-01', str(year) + '-08-31')
        .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 40)
        .sort('CLOUDY_PIXEL_PERCENTAGE'))

    count = collection.size().getInfo()
    if count == 0:
        return None

    image = collection.first()
    ndsi = image.normalizedDifference(['B3', 'B11']).rename('NDSI')

    mean_ndsi = ndsi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=point_region,
        scale=20,
        maxPixels=1e9
    )
    return mean_ndsi.getInfo().get('NDSI')

print("=== Ronti Peak summer NDSI (snow/ice cover index), 2016-2020 ===")
print("Year, Mean NDSI, Status")

results = {}
for year in years:
    val = get_summer_ndsi(region, year)
    results[year] = val

valid = {y: v for y, v in results.items() if v is not None}
if len(valid) >= 2:
    mean_all = sum(valid.values()) / len(valid)
    std_all = (sum((v - mean_all)**2 for v in valid.values()) / len(valid)) ** 0.5
else:
    mean_all, std_all = None, None

for year in years:
    val = results[year]
    if val is None:
        print(str(year) + ", n/a, no clear image")
        continue

    if std_all and std_all > 0 and val < (mean_all - 1.0 * std_all):
        status = "LOW SNOW/ICE (possible melt anomaly)"
    else:
        status = "normal"

    print(str(year) + ", " + str(round(val, 4)) + ", " + status)

print("")
print("Baseline mean NDSI: " + str(round(mean_all, 4) if mean_all else "n/a"))
print("Baseline std dev: " + str(round(std_all, 4) if std_all else "n/a"))
