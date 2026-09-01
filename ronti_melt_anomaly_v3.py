import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

years = range(2016, 2021)

def get_summer_ndsi(point_region, year):
    # Wider window: May through October, catches more chances of clear skies
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(point_region)
        .filterDate(str(year) + '-05-01', str(year) + '-10-31')
        .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 30)
        .sort('CLOUDY_PIXEL_PERCENTAGE'))

    count = collection.size().getInfo()
    if count == 0:
        return None, None, 0

    # Use up to the 5 least-cloudy images and average their NDSI,
    # instead of trusting a single snapshot
    n_images = min(count, 5)
    images = collection.limit(n_images).toList(n_images)

    ndsi_values = []
    cloud_values = []
    for i in range(n_images):
        img = ee.Image(images.get(i))
        cloud_pct = img.get('CLOUDY_PIXEL_PERCENTAGE').getInfo()
        ndsi = img.normalizedDifference(['B3', 'B11']).rename('NDSI')
        mean_val = ndsi.reduceRegion(
            reducer=ee.Reducer.mean(), geometry=point_region, scale=20, maxPixels=1e9
        ).getInfo().get('NDSI')
        if mean_val is not None:
            ndsi_values.append(mean_val)
            cloud_values.append(cloud_pct)

    if not ndsi_values:
        return None, None, 0

    avg_ndsi = sum(ndsi_values) / len(ndsi_values)
    avg_cloud = sum(cloud_values) / len(cloud_values)
    return avg_ndsi, avg_cloud, len(ndsi_values)

print("=== Ronti Peak summer NDSI, 2016-2020 (May-Oct, multi-image average) ===")
print("Year, Mean NDSI, AvgCloud%, ImagesUsed, Status")

results = {}
for year in years:
    val, cloud, n = get_summer_ndsi(region, year)
    results[year] = (val, cloud, n)

valid = {y: v[0] for y, v in results.items() if v[0] is not None}
if len(valid) >= 2:
    mean_all = sum(valid.values()) / len(valid)
    std_all = (sum((v - mean_all)**2 for v in valid.values()) / len(valid)) ** 0.5
else:
    mean_all, std_all = None, None

for year in years:
    val, cloud, n = results[year]
    if val is None:
        print(str(year) + ", n/a, n/a, 0, no usable images found")
        continue

    flag = ""
    if std_all and std_all > 0 and val < (mean_all - 1.0 * std_all):
        flag = " LOW SNOW/ICE (possible melt anomaly)"

    print(str(year) + ", " + str(round(val, 4)) + ", " + str(round(cloud,1)) + "%, " + str(n) + flag)

print("")
print("Baseline mean NDSI: " + (str(round(mean_all, 4)) if mean_all else "n/a"))
print("Baseline std dev: " + (str(round(std_all, 4)) if std_all else "n/a"))
