import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

years = range(2015, 2022)  # MODIS goes back much further than Sentinel-2, worth using that

print("=== Ronti Peak summer MODIS NDSI Snow Cover, 2015-2021 ===")
print("Year, MeanNDSI_SnowCover, ImagesUsed, Status")

results = {}
for year in years:
    collection = (ee.ImageCollection('MODIS/061/MOD10A1')
        .filterBounds(region)
        .filterDate(str(year) + '-06-01', str(year) + '-08-31'))

    count = collection.size().getInfo()
    if count == 0:
        results[year] = (None, 0)
        continue

    mean_img = collection.select('NDSI_Snow_Cover').mean()
    val = mean_img.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=500, maxPixels=1e9
    ).getInfo().get('NDSI_Snow_Cover')

    results[year] = (val, count)

valid = {y: v[0] for y, v in results.items() if v[0] is not None}
mean_all = sum(valid.values()) / len(valid)
std_all = (sum((v - mean_all)**2 for v in valid.values()) / len(valid)) ** 0.5

for year in years:
    val, n = results[year]
    if val is None:
        print(str(year) + ", n/a, 0, no data")
        continue
    flag = ""
    if val < (mean_all - 1.0 * std_all):
        flag = " LOW SNOW/ICE (possible melt anomaly)"
    print(str(year) + ", " + str(round(val, 2)) + ", " + str(n) + " images" + flag)

print("")
print("Baseline mean: " + str(round(mean_all, 2)))
print("Baseline std dev: " + str(round(std_all, 2)))
