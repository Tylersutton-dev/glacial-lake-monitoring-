import ee
import csv
from datetime import datetime

ee.Initialize(project='draft-glacier')

sites = {
    "PDGL_01": {"point": ee.Geometry.Point([87.945, 27.781]), "buffer": 800, "rank": "I"},
    "PDGL_02": {"point": ee.Geometry.Point([87.934, 27.790]), "buffer": 800, "rank": "III"},
    "PDGL_03": {"point": ee.Geometry.Point([87.893, 27.694]), "buffer": 800, "rank": "III"},
    "PDGL_04": {"point": ee.Geometry.Point([87.749, 27.816]), "buffer": 800, "rank": "I"},
    "PDGL_05": {"point": ee.Geometry.Point([87.596, 27.705]), "buffer": 800, "rank": "I"},
    "PDGL_06": {"point": ee.Geometry.Point([87.632, 27.729]), "buffer": 800, "rank": "III"},
    "PDGL_07": {"point": ee.Geometry.Point([87.771, 27.926]), "buffer": 800, "rank": "I"},
    "PDGL_08": {"point": ee.Geometry.Point([87.636, 28.093]), "buffer": 800, "rank": "I"},
    "PDGL_09": {"point": ee.Geometry.Point([87.626, 28.052]), "buffer": 800, "rank": "I"},
    "PDGL_10": {"point": ee.Geometry.Point([87.563, 28.178]), "buffer": 800, "rank": "III"},
    "PDGL_11": {"point": ee.Geometry.Point([87.591, 28.229]), "buffer": 1000, "rank": "II"},
    "PDGL_12": {"point": ee.Geometry.Point([87.930, 27.949]), "buffer": 800, "rank": "I"},
    "PDGL_13": {"point": ee.Geometry.Point([88.002, 27.928]), "buffer": 1000, "rank": "I"},
    "PDGL_14": {"point": ee.Geometry.Point([88.019, 27.928]), "buffer": 800, "rank": "I"},
    "PDGL_15": {"point": ee.Geometry.Point([88.066, 27.933]), "buffer": 800, "rank": "I"},
    "PDGL_16": {"point": ee.Geometry.Point([88.075, 27.946]), "buffer": 1000, "rank": "I"},
    "PDGL_17": {"point": ee.Geometry.Point([88.288, 28.017]), "buffer": 800, "rank": "II"},
    "PDGL_18": {"point": ee.Geometry.Point([86.304, 28.374]), "buffer": 1000, "rank": "II"},
    "PDGL_19": {"point": ee.Geometry.Point([87.134, 28.069]), "buffer": 800, "rank": "I"},
    "PDGL_20": {"point": ee.Geometry.Point([87.095, 27.829]), "buffer": 800, "rank": "II"},
    "Lower Barun": {"point": ee.Geometry.Point([87.092, 27.798]), "buffer": 1000, "rank": "I"},
    "PDGL_22": {"point": ee.Geometry.Point([86.977, 27.711]), "buffer": 800, "rank": "I"},
    "Chamlang": {"point": ee.Geometry.Point([86.958, 27.755]), "buffer": 800, "rank": "II"},
    "Hongu 2": {"point": ee.Geometry.Point([86.957, 27.783]), "buffer": 800, "rank": "I"},
    "Hongu 1": {"point": ee.Geometry.Point([86.935, 27.838]), "buffer": 800, "rank": "I"},
    "PDGL_26": {"point": ee.Geometry.Point([86.928, 27.850]), "buffer": 800, "rank": "I"},
    "PDGL_27": {"point": ee.Geometry.Point([86.917, 27.832]), "buffer": 800, "rank": "I"},
    "PDGL_28": {"point": ee.Geometry.Point([86.858, 27.687]), "buffer": 800, "rank": "I"},
    "Imja Tsho": {"point": ee.Geometry.Point([86.925, 27.898]), "buffer": 1500, "rank": "I"},
    "Lumding": {"point": ee.Geometry.Point([86.612, 27.779]), "buffer": 1000, "rank": "I"},
    "Tsho Rolpa": {"point": ee.Geometry.Point([86.476, 27.861]), "buffer": 2000, "rank": "I"},
    "PDGL_32": {"point": ee.Geometry.Point([86.447, 27.946]), "buffer": 800, "rank": "I"},
    "PDGL_33": {"point": ee.Geometry.Point([86.500, 28.033]), "buffer": 800, "rank": "II"},
    "PDGL_34": {"point": ee.Geometry.Point([86.520, 28.073]), "buffer": 800, "rank": "I"},
    "PDGL_35": {"point": ee.Geometry.Point([86.530, 28.135]), "buffer": 800, "rank": "II"},
    "PDGL_36": {"point": ee.Geometry.Point([86.532, 28.185]), "buffer": 800, "rank": "I"},
    "PDGL_37": {"point": ee.Geometry.Point([86.371, 28.238]), "buffer": 800, "rank": "I"},
    "PDGL_38": {"point": ee.Geometry.Point([86.314, 28.194]), "buffer": 800, "rank": "I"},
    "PDGL_39": {"point": ee.Geometry.Point([86.157, 28.303]), "buffer": 800, "rank": "I"},
    "PDGL_40": {"point": ee.Geometry.Point([86.225, 28.346]), "buffer": 800, "rank": "II"},
    "PDGL_41": {"point": ee.Geometry.Point([85.870, 28.360]), "buffer": 800, "rank": None},
    "PDGL_42": {"point": ee.Geometry.Point([85.838, 28.322]), "buffer": 800, "rank": None},
    "PDGL_43": {"point": ee.Geometry.Point([85.630, 28.162]), "buffer": 800, "rank": None},
    "PDGL_44": {"point": ee.Geometry.Point([85.494, 28.508]), "buffer": 800, "rank": None},
    "PDGL_45": {"point": ee.Geometry.Point([84.485, 28.488]), "buffer": 800, "rank": None},
    "PDGL_46": {"point": ee.Geometry.Point([82.673, 29.802]), "buffer": 800, "rank": None},
    "PDGL_47": {"point": ee.Geometry.Point([80.387, 30.445]), "buffer": 800, "rank": None},
}

years = range(2016, 2025)  # full 9-year range, same as your original work

def get_lake_area_median(point, buffer_m, year):
    collection = (ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterBounds(point)
        .filterDate(str(year)+'-01-01', str(year)+'-12-31')
        .filterMetadata('CLOUD_COVER', 'less_than', 50)
        .sort('CLOUD_COVER'))
    count = collection.size().getInfo()
    if count == 0:
        return None, 0
    n_images = min(count, 6)  # full 6-image median, same as your working version
    images = collection.limit(n_images).toList(n_images)
    areas = []
    for i in range(n_images):
        img = ee.Image(images.get(i))
        ndwi = img.normalizedDifference(['SR_B3', 'SR_B5']).rename('NDWI')
        water = ndwi.gt(0.2)
        area = water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
            reducer=ee.Reducer.sum(), geometry=point.buffer(buffer_m), scale=30, maxPixels=1e9
        ).getInfo().get('NDWI')
        if area is not None and area > 0:
            areas.append(area)
    if not areas:
        return None, 0
    areas.sort()
    return areas[len(areas)//2], len(areas)

rows = []
site_names = list(sites.keys())
total = len(site_names)

for i, name in enumerate(site_names):
    info = sites[name]
    print(f"[{i+1}/{total}] Processing {name}...")
    lake_results = {}
    for year in years:
        val, n = get_lake_area_median(info['point'], info['buffer'], year)
        lake_results[year] = (val, n)

    valid = sorted([v[0] for v in lake_results.values() if v[0] is not None])
    site_median = valid[len(valid)//2] if valid else None

    for year in years:
        val, n = lake_results[year]
        if val is None:
            status = "no_image"
        elif site_median and val < 0.1 * site_median:
            status = "contaminated"
        else:
            status = "ok"
        rows.append({
            'site': name, 'year': year, 'rank': info['rank'],
            'lake_area_m2': val if val is not None else '',
            'lake_status': status, 'images_used': n,
            'last_updated': datetime.now().isoformat()
        })

    # Save after every site so an interruption doesn't cost you the whole run
    with open('himalaya_47lakes_full.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['site','year','rank','lake_area_m2','lake_status','images_used','last_updated'])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> progress saved ({(i+1)}/{total} sites complete)")

print("Done. Full dataset saved to himalaya_47lakes_full.csv")
