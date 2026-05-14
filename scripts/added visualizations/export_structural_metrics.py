"""Export structural network metrics."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import pickle
import math
import numpy as np
import pandas as pd
from pathlib import Path

                                                                             
BASE = PROJECT_ROOT
PKL  = BASE / "data" / "model_outputs" / "networks" / "provincial_energy_networks.pkl"
OUT_DIR = BASE / "outputs" / "tables" / "figure_data"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "structural_metrics_data.xlsx"

print("Loading network data...")
with open(PKL, "rb") as f:
    all_networks = pickle.load(f)
print("Loaded.")

                                                                            
energy_categories = {
}
supply_nodes = {
}

                                                                            
province_name_mapping = {
}
HIGHLIGHT_CN = {'Liaoning', 'Qinghai'}

ALL_YEARS = list(range(2001, 2021))

                                                                            
def get_metrics(G):
    cat_flow = {cat: 0.0 for cat in energy_categories}
    total_supply_flow = 0.0
    for u, v, d in G.edges(data=True):
        w = abs(d.get("weight", 0))
        if u in supply_nodes:
            for cat, items in energy_categories.items():
                if v in items:
                    cat_flow[cat] += w
                    total_supply_flow += w
                    break
    shares = {cat: (cat_flow[cat] / total_supply_flow if total_supply_flow > 0 else 0)
              for cat in energy_categories}
    entropy = -sum(s * math.log(s) for s in shares.values() if s > 0)

    supply_src = {}
    for u, v, d in G.edges(data=True):
        if u in supply_nodes:
            supply_src[u] = supply_src.get(u, 0) + abs(d.get("weight", 0))
    total_s = sum(supply_src.values())
    hhi = sum((v / total_s) ** 2 for v in supply_src.values()) if total_s > 0 else 1.0

    return shares, entropy, hhi

                                                                            
print("Computing metrics for all provinces...")
rows = []
for grid_name, grid_data in all_networks.items():
    sample_year = list(grid_data.keys())[0]
    for prov_cn in grid_data[sample_year].keys():
        prov_en = province_name_mapping.get(prov_cn, prov_cn)
        panel = "Right (Liaoning & Qinghai)" if prov_cn in HIGHLIGHT_CN else "Left (all others)"
        for yr in ALL_YEARS:
            try:
                G = grid_data[yr][prov_cn]
                shares, ent, hhi = get_metrics(G)
                row = {
                    "Province_CN":   prov_cn,
                    "Province_EN":   prov_en,
                    "Year":          yr,
                    "Shannon_Entropy": ent,
                    "HHI":           hhi,
                    "Panel":         panel,
                }
                                         
                for cat, s in shares.items():
                    row[f"Share_{cat}"] = s
                rows.append(row)
            except KeyError:
                rows.append({
                    "Province_CN":   prov_cn,
                    "Province_EN":   prov_en,
                    "Year":          yr,
                    "Shannon_Entropy": np.nan,
                    "HHI":           np.nan,
                    "Panel":         panel,
                    **{f"Share_{cat}": np.nan for cat in energy_categories},
                })

df = pd.DataFrame(rows)
df = df.sort_values(["Province_EN", "Year"]).reset_index(drop=True)
print(f"Total rows: {len(df)}")
print(df.head())

                                                                            
                    
                                                                          
                                           

df_left  = df[df["Panel"] == "Left (all others)"].copy()
df_right = df[df["Panel"] == "Right (Liaoning & Qinghai)"].copy()

                            
df_left_annual = (
    df_left.groupby("Year")[["Shannon_Entropy", "HHI"]]
    .agg(["mean", "std", "min", "max"])
    .round(4)
)
df_left_annual.columns = ['_'.join(c) for c in df_left_annual.columns]
df_left_annual = df_left_annual.reset_index()

with pd.ExcelWriter(OUT_FILE, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="All_Data", index=False)
    df_left.to_excel(writer, sheet_name="Left_Panel_All_Provinces", index=False)
    df_right.to_excel(writer, sheet_name="Right_Panel_Liao_Qing", index=False)
    df_left_annual.to_excel(writer, sheet_name="Left_Panel_Annual_Mean", index=False)

print(f"\nSaved to: {OUT_FILE}")
