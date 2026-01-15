import requests
import pandas as pd
import sys

# 1. Configuration for Islamabad
LAT = 33.6844
LON = 73.0479

# 2. Setup the Request
# We add a "User-Agent" so the server treats us like a browser, not a bot.
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

# Base URL for ISRIC SoilGrids v2
base_url = "https://rest.isric.org/soilgrids/v2.0/properties/query"

# Parameters
params = {
    "lat": LAT,
    "lon": LON,
    "property": ["clay", "sand", "bdod", "soc", "wv33", "wv1500"],
    "depth": ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"],
    "value": "mean"
}

print(f"Fetching soil data for Lat: {LAT}, Lon: {LON} from ISRIC SoilGrids...")

try:
    response = requests.get(base_url, params=params, headers=headers)
    # Check if the server gave a valid response (Code 200)
    if response.status_code != 200:
        print(f"\n[ERROR] Server returned status code: {response.status_code}")
        print("Server Message:", response.text[:500]) # Print first 500 chars of error
        sys.exit(1)
    data = response.json()

except Exception as e:
    print(f"\n[CRITICAL ERROR] Could not connect or parse JSON.")
    print(f"Details: {e}")
    sys.exit(1)

# 3. Helper function
def get_val(layer_name, prop):
    try:
        layers = data['properties']['layers']
        for l in layers:
            if l['name'] == prop:
                for depth in l['depths']:
                    if depth['label'] == layer_name:
                        return depth['values']['mean']
    except:
        return -999
    return -999

# 4. Standard Layers
layers_map = [
    {"label": "0-5cm",    "thick": 0.05},
    {"label": "5-15cm",   "thick": 0.10},
    {"label": "15-30cm",  "thick": 0.15},
    {"label": "30-60cm",  "thick": 0.30},
    {"label": "60-100cm", "thick": 0.40},
    {"label": "100-200cm","thick": 1.00}
]

rows = []

# 5. Process Data
for idx, layer in enumerate(layers_map):
    clay_raw = get_val(layer['label'], 'clay')   
    sand_raw = get_val(layer['label'], 'sand')   
    bd_raw   = get_val(layer['label'], 'bdod')   
    soc_raw  = get_val(layer['label'], 'soc')    
    fc_raw   = get_val(layer['label'], 'wv33')   
    pwp_raw  = get_val(layer['label'], 'wv1500') 

    # If API returns None, handle it
    if clay_raw is None: clay_raw = -999

    # Conversions
    clay = clay_raw / 10.0 if clay_raw != -999 else 21.0 # Fallback default
    sand = sand_raw / 10.0 if sand_raw != -999 else 15.0
    bd   = bd_raw / 100.0 if bd_raw != -999 else 1.45
    org  = (soc_raw / 100.0) * 1.724 if soc_raw != -999 else 0.50
    fc   = fc_raw / 1000.0 if fc_raw != -999 else 0.280
    pwp  = pwp_raw / 1000.0 if pwp_raw != -999 else 0.120

    rows.append({
        "LAYER": idx + 1,
        "THICK": layer['thick'],
        "CLAY": clay,
        "SAND": sand,
        "ORGANIC": org,
        "BD": bd,
        "FC": fc,
        "PWP": pwp,
        "SON": -999, "NO3": 10, "NH4": 1, "BYP_H": 0.0, "BYP_V": 0.0
    })

# 6. Print Output
print("\nGenerated Soil Data (ISRIC Source):")
print("-" * 30)
print(f"CURVE_NUMBER        75")
print(f"SLOPE               0")
print(f"TOTAL_LAYERS        {len(rows)}")
print("LAYER   THICK   CLAY    SAND    ORGANIC BD      FC      PWP     SON     NO3     NH4     BYP_H   BYP_V")
print("#       m       %       %       %       Mg/m3   m3/m3   m3/m3   kg/ha   kg/ha   kg/ha   -       -")

for r in rows:
    print(f"{r['LAYER']:<8}"
          f"{r['THICK']:<8.2f}"
          f"{r['CLAY']:<8.1f}"
          f"{r['SAND']:<8.1f}"
          f"{r['ORGANIC']:<8.2f}"
          f"{r['BD']:<8.2f}"
          f"{r['FC']:<8.3f}"
          f"{r['PWP']:<8.3f}"
          f"{r['SON']:<8}"
          f"{r['NO3']:<8}"
          f"{r['NH4']:<8}"
          f"{r['BYP_H']:<8}"
          f"{r['BYP_V']:<8}")