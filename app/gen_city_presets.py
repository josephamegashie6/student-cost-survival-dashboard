"""
gen_city_presets.py — Generate CITY_EXPENSE_PRESETS and CITY_MIN_WAGE from metro_benchmarks.csv
Run once to print the dict literals for pasting into app.py
"""
import pandas as pd, os

df = pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "data", "metro_benchmarks.csv"))

# Build CITY_EXPENSE_PRESETS
print("CITY_EXPENSE_PRESETS = {")
for _, r in df.iterrows():
    metro = r["metro"]
    rent = int(r["rent_1br"])
    utilities = int(r["utilities"])
    food = int(r["groceries"])
    transport = int(r["transport_monthly"])
    internet = int(r["internet"])
    misc_basic = int(r["misc_basic"])
    discretionary = int(r["discretionary"])
    print(f'    "{metro}": {{"rent": {rent}, "utilities": {utilities}, "food": {food}, "transport": {transport}, "phone_internet": {internet}, "misc_basic": {misc_basic}, "discretionary": {discretionary}}},')
print("}")
print()

# Build CITY_MIN_WAGE (approximate by cost tier)
tier_wage = {
    "Very High": 17.00,
    "High": 15.50,
    "Medium": 14.00,
    "Low": 12.00,
    "Very Low": 10.00,
}
print("CITY_MIN_WAGE = {")
for _, r in df.iterrows():
    metro = r["metro"]
    wage = tier_wage.get(r["cost_tier"], 12.00)
    print(f'    "{metro}": {wage},')
print("}")
