import ee

ee.Initialize(project='draft-glacier')

def get_lake_area_sar_clean(point, buffer_m, start_date, end_date, pass_direction='ASCENDING'):
    """Extracts shadow-masked water area (m^2) for a given date window."""
    dem = ee.Image("USGS/SRTMGL1_003")
    slope = ee.Terrain.slope(dem)

    collection = (ee.ImageCollection('COPERNICUS/S1_GRD')
        .filterBounds(point.buffer(buffer_m))
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq('instrumentMode', 'IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        .filter(ee.Filter.eq('orbitProperties_pass', pass_direction))
        .select(['VV', 'angle']))

    if collection.size().getInfo() == 0:
        return None

    sar_img = collection.median()
    vv = sar_img.select('VV')
    smoothed_vv = vv.focal_mean(1.5, 'circle', 'meters')

    raw_water = smoothed_vv.lt(-16.0)
    flat_terrain_mask = slope.lt(10.0)
    valid_angle_mask = sar_img.select('angle').gt(30.0)

    clean_water = raw_water.updateMask(flat_terrain_mask).updateMask(valid_angle_mask)

    area = clean_water.selfMask().multiply(ee.Image.pixelArea()).reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=point.buffer(buffer_m),
        scale=10,
        maxPixels=1e9
    )

    return area.getInfo().get('VV')


# --- Target Location: Imja Tsho ---
imja_point = ee.Geometry.Point([86.925, 27.898])
buffer_distance = 1500

# --- Consecutive Date Windows (12-Day Orbit Repeat) ---
# Pass 1: Baseline pass
pass1_start, pass1_end = '2024-06-18', '2024-06-30'
# Pass 2: Current pass
pass2_start, pass2_end = '2024-07-01', '2024-07-13'

print(f"Analyzing Pass 1 ({pass1_start} to {pass1_end})...")
area_pass1 = get_lake_area_sar_clean(imja_point, buffer_distance, pass1_start, pass1_end)

print(f"Analyzing Pass 2 ({pass2_start} to {pass2_end})...")
area_pass2 = get_lake_area_sar_clean(imja_point, buffer_distance, pass2_start, pass2_end)

if area_pass1 and area_pass2:
    # Calculate Percentage Change
    delta_area_m2 = area_pass2 - area_pass1
    pct_change = (delta_area_m2 / area_pass1) * 100

    print("\n==========================================")
    print(f"Pass 1 Surface Area : {area_pass1:,.2f} m²")
    print(f"Pass 2 Surface Area : {area_pass2:,.2f} m²")
    print(f"Absolute Area Delta : {delta_area_m2:+,.2f} m²")
    print(f"Relative Area Change: {pct_change:+.2f}%")
    print("==========================================")

    # --- Early Warning Trigger Logic ---
    if pct_change <= -25.0:
        print("🚨 RED ALERT: Rapid Lake Drainage Detected (Potential Active Outburst/Breach)!")
    elif pct_change >= 15.0:
        print("⚠️ ORANGE WARNING: Rapid Lake Expansion Detected (Accelerated Inflow/Pressure)!")
    else:
        print("✅ STATUS: Normal Surface Area Variance (Within Safe Operational Limits)")

else:
    print("Error: Could not retrieve SAR passes for one or both date ranges.")
