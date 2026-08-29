import ee

ee.Initialize(project='draft-glacier')

lakes = {
    'Lower Barun':  {'point': ee.Geometry.Point([87.092, 27.798]), 'buffer': 1000, 'dam_type': 'moraine', 'rank': 'I'},
    'Chamlang':     {'point': ee.Geometry.Point([86.958, 27.755]), 'buffer': 800,  'dam_type': 'moraine', 'rank': 'II'},
    'Hongu 2':      {'point': ee.Geometry.Point([86.957, 27.783]), 'buffer': 800,  'dam_type': 'moraine', 'rank': 'I'},
    'Hongu 1':      {'point': ee.Geometry.Point([86.935, 27.838]), 'buffer': 800,  'dam_type': 'moraine', 'rank': 'I'},
    'Imja Tsho':    {'point': ee.Geometry.Point([86.925, 27.898]), 'buffer': 1500, 'dam_type': 'moraine', 'rank': 'I'},
    'Lumding':      {'point': ee.Geometry.Point([86.612, 27.779]), 'buffer': 1000, 'dam_type': 'moraine', 'rank': 'I'},
    'Tsho Rolpa':   {'point': ee.Geometry.Point([86.476, 27.861]), 'buffer': 2000, 'dam_type': 'moraine', 'rank': 'I'},
    'PDGL_32':      {'point': ee.Geometry.Point([86.447, 27.946]), 'buffer': 800,  'dam_type': 'moraine', 'rank': 'I'},
    'PDGL_34':      {'point': ee.Geometry.Point([86.520, 28.073]), 'buffer': 800,  'dam_type': 'moraine', 'rank': 'I'},
    'PDGL_37':      {'point': ee.Geometry.Point([86.371, 28.238]), 'buffer': 800,  'dam_type': 'moraine', 'rank': 'I'}
}

DAM_RISK_WEIGHT = {'moraine': 1.5, 'ice': 1.2, 'bedrock': 0.5, 'unknown': 1.0}

years = range(2016, 2025)  # Sentinel-2 archive starts mid-2015

def get_area(point, buffer_m, start, end):
    collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(point).filterDate(start, end).sort('CLOUDY_PIXEL_PERCENTAGE'))
    if collection.size().getInfo() == 0:
        return None
    image = collection.first()
    ndwi = image.normalizedDifference(['B3', 'B8']).rename('NDWI')
    water = ndwi.gt(0.2)
    area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=point.buffer(buffer_m), scale=10, maxPixels=1e9)
    return area.getInfo().get('NDWI')

print("Lake, DamType, Rank, CurrentSize(km2), GrowthRate(%), RiskScore")
for name, info in lakes.items():
    results = {}
    for year in years:
        results[year] = get_area(info['point'], info['buffer'], str(year)+'-01-01', str(year)+'-12-31')

    valid_years = sorted([y for y in results if results[y] and results[y] > 0])
    if len(valid_years) < 4:
        print(name + ", " + info['dam_type'] + ", " + info['rank'] + ", n/a, n/a, insufficient data")
        continue

    first_group = sorted([results[y] for y in valid_years[:3]])
    last_group = sorted([results[y] for y in valid_years[-3:]])
    first_val = first_group[len(first_group)//2]
    last_val = last_group[len(last_group)//2]

    current_size_km2 = last_val / 1_000_000
    growth_pct = ((last_val - first_val) / first_val) * 100
    size_factor = min(current_size_km2 / 0.02, 10)
    risk_score = growth_pct * DAM_RISK_WEIGHT[info['dam_type']] * size_factor

    print(name + ", " + info['dam_type'] + ", " + info['rank'] + ", " +
          str(round(current_size_km2, 3)) + ", " +
          str(round(growth_pct, 1)) + ", " +
          str(round(risk_score, 1)))
