"""
update_city_presets.py — Replace hardcoded city presets in app.py with CSV-driven versions
"""
import pandas as pd
import re

# Load metro data
df = pd.read_csv("/home/ubuntu/sfid/data/metro_benchmarks.csv")

# Build CITY_EXPENSE_PRESETS string
tier_wage = {
    "Very High": 17.00,
    "High": 15.50,
    "Medium": 14.00,
    "Low": 12.00,
    "Very Low": 10.00,
}

preset_lines = ["CITY_EXPENSE_PRESETS = {"]
wage_lines = ["CITY_MIN_WAGE = {"]
for _, r in df.iterrows():
    metro = r["metro"].replace('"', '\\"')
    rent = int(r["rent_1br"])
    utilities = int(r["utilities"])
    food = int(r["groceries"])
    transport = int(r["transport_monthly"])
    internet = int(r["internet"])
    misc_basic = int(r["misc_basic"])
    discretionary = int(r["discretionary"])
    preset_lines.append(
        f'    "{metro}": {{"rent": {rent}, "utilities": {utilities}, "food": {food}, '
        f'"transport": {transport}, "phone_internet": {internet}, "misc_basic": {misc_basic}, '
        f'"discretionary": {discretionary}}},'
    )
    wage = tier_wage.get(r["cost_tier"], 12.00)
    wage_lines.append(f'    "{metro}": {wage},')

preset_lines.append("}")
wage_lines.append("}")

new_presets = "\n".join(preset_lines)
new_wages = "\n".join(wage_lines)

# Read app.py
with open("/home/ubuntu/sfid/app/app.py", "r") as f:
    content = f.read()

# Replace CITY_MIN_WAGE block
content = re.sub(
    r'CITY_MIN_WAGE\s*=\s*\{[^}]+\}',
    new_wages,
    content,
    flags=re.DOTALL
)

# Replace CITY_EXPENSE_PRESETS block
content = re.sub(
    r'CITY_EXPENSE_PRESETS\s*=\s*\{[^}]+\}',
    new_presets,
    content,
    flags=re.DOTALL
)

with open("/home/ubuntu/sfid/app/app.py", "w") as f:
    f.write(content)

print(f"Done. Replaced CITY_EXPENSE_PRESETS ({len(df)} metros) and CITY_MIN_WAGE ({len(df)} metros).")
