import rasterio
import numpy as np
import cv2

def load_grayscale(path):
    with rasterio.open(path) as src:
        img = src.read([1,2,3]).astype(np.float32)
        gray = np.mean(img, axis=0)
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        pixel_size_m = src.res[0]
        return gray, pixel_size_m

def track_displacement(img1, img2, pixel_size_m, template_size=32, step=64, search_margin=20):
    h, w = img1.shape
    half_t = template_size // 2
    results = []

    for y in range(half_t + search_margin, h - half_t - search_margin, step):
        for x in range(half_t + search_margin, w - half_t - search_margin, step):
            template = img1[y-half_t:y+half_t, x-half_t:x+half_t]

            search_area = img2[y-half_t-search_margin : y+half_t+search_margin,
                                x-half_t-search_margin : x+half_t+search_margin]

            # Strict size check on BOTH dimensions before matching
            if (template.shape[0] == 0 or template.shape[1] == 0 or
                search_area.shape[0] <= template.shape[0] or
                search_area.shape[1] <= template.shape[1]):
                continue

            match = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(match)

            if max_val < 0.5:
                continue

            dx_px = max_loc[0] - search_margin
            dy_px = max_loc[1] - search_margin
            displacement_px = np.sqrt(dx_px**2 + dy_px**2)
            displacement_m = displacement_px * pixel_size_m

            results.append({'x': x, 'y': y, 'displacement_m': displacement_m, 'confidence': max_val})

    return results

def summarize(results, label):
    if not results:
        print(label + ": no confident matches found")
        return

    displacements = [r['displacement_m'] for r in results]
    median_disp = np.median(displacements)
    max_disp = np.max(displacements)
    anomaly_threshold = median_disp * 5 if median_disp > 0 else 1.0

    anomalies = [r for r in results if r['displacement_m'] > anomaly_threshold]

    print("=== " + label + " ===")
    print("Patches tracked: " + str(len(results)))
    print("Median displacement: " + str(round(median_disp, 2)) + " m")
    print("Max displacement: " + str(round(max_disp, 2)) + " m")
    print("Anomalous patches (>5x median): " + str(len(anomalies)))
    if anomalies:
        worst = max(anomalies, key=lambda r: r['displacement_m'])
        print("  Worst anomaly at pixel (" + str(worst['x']) + ", " + str(worst['y']) +
              "): " + str(round(worst['displacement_m'], 2)) + " m")
    print("")

img_2018, res = load_grayscale('/Users/tylersutton/ronti_images/ronti_peak_2018.tif')
img_2019, _ = load_grayscale('/Users/tylersutton/ronti_images/ronti_peak_2019.tif')
img_2020, _ = load_grayscale('/Users/tylersutton/ronti_images/ronti_peak_2020.tif')

print("Image size: " + str(img_2018.shape))
print("Pixel resolution: " + str(res) + " m/pixel")
print("")

results_18_19 = track_displacement(img_2018, img_2019, res)
summarize(results_18_19, "2018 -> 2019")

results_19_20 = track_displacement(img_2019, img_2020, res)
summarize(results_19_20, "2019 -> 2020")
