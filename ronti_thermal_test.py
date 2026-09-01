import ee

ee.Initialize(project='draft-glacier')

ronti_peak = ee.Geometry.Point([79.719, 30.369])
region = ronti_peak.buffer(3000)

years = range(2015, 2022)

print("=== Ronti Peak summer surface temperature (Landsat thermal), 2015-2021 ===")
print("Year, MeanSurfaceTemp(C), ImagesUsed, Status")

results = {}
for year in years:
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(region)
        .filterDate(str(year) + '-06-01', str(year) + '-08-31')
        .filterMetadata('CLOUD_COVER', 'less_than', 50))

    count = collection.size().getInfo()
    if count == 0:
        results[year] = (None, 0)
        continue

    # ST_B10 is Landsat 8's thermal band, needs scaling to real Celsius
    thermal = collection.select('ST_B10').mean()
    temp_kelvin = thermal.multiply(0.00341802).add(149.0)
    temp_celsius = temp_kelvin.subtract(273.15)

    val = temp_celsius.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=region, scale=30, maxPixels=1e9
    ).getInfo().get('ST_B10')

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
    if val > (mean_all + 1.0 * std_all):
        flag = " ANOMALOUSLY WARM"
    print(str(year) + ", " + str(round(val, 2)) + ", " + str(n) + " images" + flag)

print("")
print("Baseline mean: " + str(round(mean_all, 2)) + " C")
print("Baseline std dev: " + str(round(std_all, 2)) + " C")
