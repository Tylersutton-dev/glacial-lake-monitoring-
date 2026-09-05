import ee

ee.Initialize(project='draft-glacier')

print("Step 1: defining region...")
mountain_region = ee.Geometry.Rectangle([86.6, 27.6, 87.2, 28.1])

print("Step 2: generating random points...")
mountain_points = ee.FeatureCollection.randomPoints(
    region=mountain_region, points=100, seed=42, maxError=100
)

print("Step 3: loading elevation data...")
dem = ee.Image("USGS/SRTMGL1_003").rename("elevation")

print("Step 4: mapping elevation onto points (this is the likely slow/risky step)...")
mountain_points = mountain_points.map(
    lambda feature: feature.set(
        "elevation",
        dem.reduceRegion(
            reducer=ee.Reducer.first(), geometry=feature.geometry(), scale=30, maxPixels=1000
        ).get("elevation")
    )
)

print("Step 5: filtering to high elevation...")
high_mountain_points = mountain_points.filter(ee.Filter.gte("elevation", 4500))

print("Step 6: fetching results (this triggers everything above to actually run)...")
mountain_features = high_mountain_points.limit(5).getInfo()["features"]

print(f"Done. Found {len(mountain_features)} high-elevation points.")
for f in mountain_features:
    print(f["geometry"]["coordinates"])
