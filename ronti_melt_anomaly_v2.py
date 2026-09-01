import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

years = range(2016, 2021)

def get_summer_ndsi(point_region, year):
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(point_region)
        .filterDate(str(year) + '-06-01', str(year) + '-09-30')  # wider window
        .sort('CLOUDY_PIXEL_PERCENTAGE'))

    count = collection.size().getInfo()
    if count == 0:
        return None, None

    image = collection.first()
    cloud_pct = image.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
    ndsi = image.normalizedDifference(['B3', 'B11']).rename('NDSI')

    mean_ndsi = ndsi.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=point_region, scale=20, maxPixels=1e9)
    return mean_ndsi.getInfo().get('NDSI'), cloud_pct

print("=== Ronti Peak summer NDSI, 2016-2020 (widened June-Sept window) ===")
print("Year, Mean NDSI, Cloud%, Status")

results = {}
for year in years:
    val, cloud = get_summer_ndsi(region, year)
    results[year] = (val, cloud)

valid = {y: v[0] for y, v in results.items() if v[0] is not None}
if len(valid) >= 2:
    mean_all = sum(valid.values()) / len(valid)
    std_all = (sum((v - mean_all)**2 for v in valid.values()) / len(valid)) ** 0.5
else:
    mean_all, std_all = None, None

for year in years:
    val, cloud = results[year]
    if val is None:
        print(str(year) + ", n/a, n/a, no image found")
        continue

    flag = ""
    if std_all and std_all > 0 and val < (mean_all - 1.0 * std_all):
        flag = " LOW SNOW/ICE (possible melt anomaly)"

    cloud_note = "cloud:" + str(round(cloud,1)) + "%"
    reliability = " [high cloud, treat cautiously]" if cloud and cloud > 50 else ""

    print(str(year) + ", " + str(round(val, 4)) + ", " + cloud_note + flag + reliability)

print("")
print("Baseline mean NDSI: " + (str(round(mean_all, 4)) if mean_all else "n/a"))
print("Baseline std dev: " + (str(round(std_all, 4)) if std_all else "n/a"))
