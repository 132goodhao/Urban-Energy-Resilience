"""Export provincial energy-flow indicators."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os, pickle, math
import numpy as np
import pandas as pd

PROJECT = r"data/model_outputs"
OUT = r"outputs\tables\figure_data"

          
os.makedirs(OUT, exist_ok=True)

with open(os.path.join(PROJECT, "networks", "provincial_energy_networks.pkl"), "rb") as f:
    all_networks = pickle.load(f)

                 
GRID = {
            
            
            
            
            
            
}

         
PROVINCE_EN = {
}

PROVINCES = list(GRID.keys())
ALL_YEARS = list(range(2001, 2021))

energy_categories = {
}
supply_nodes = {
}
transformation_nodes = {
}
all_carriers = [item for items in energy_categories.values() for item in items]

TRANS_EN = {
}
SUPPLY_EN = {
}

rows_A, rows_B, rows_C = [], [], []

print(f"Processing {len(PROVINCES)} provinces x {len(ALL_YEARS)} years = {len(PROVINCES) * len(ALL_YEARS)} records...")

for prov in PROVINCES:
    grid = GRID[prov]
    prov_en = PROVINCE_EN[prov]
    for yr in ALL_YEARS:
        G = all_networks[grid][yr][prov]

                                                                                
        cat_flow = {cat: 0.0 for cat in energy_categories}
        supply_src = {}
        total_supply = 0.0

        for u, v, d in G.edges(data=True):
            w = abs(d.get("weight", 0))
            if u in supply_nodes:
                supply_src[u] = supply_src.get(u, 0) + w
                for cat, items in energy_categories.items():
                    if v in items:
                        cat_flow[cat] += w
                        total_supply  += w
                        break

        shares = {cat: (cat_flow[cat] / total_supply if total_supply > 0 else 0)
                  for cat in energy_categories}
        entropy = -sum(s * math.log(s) for s in shares.values() if s > 0)

        total_s = sum(supply_src.values())
        hhi = sum((v / total_s) ** 2 for v in supply_src.values()) if total_s > 0 else 1.0
        n_active = sum(1 for v in supply_src.values() if v > 0)

                                                                                
        tflow = {v: 0.0 for v in TRANS_EN.values()}
        for u, v, d in G.edges(data=True):
            w = abs(d.get("weight", 0))
            if v in transformation_nodes and u in all_carriers:
                en = TRANS_EN.get(v)
                if en:
                    tflow[en] += w
        trans_total = sum(tflow.values())
        trans_ratio = trans_total / total_supply if total_supply > 0 else 0

                                                                                
        row_a = {"Province": prov_en, "Province_CN": prov, "Year": yr,
                 "Total_Supply_Flow_Mtce": round(total_supply, 2)}
        for cat in energy_categories:
            row_a[f"AbsFlow_{cat}_Mtce"] = round(cat_flow[cat], 2)
        for cat in energy_categories:
            row_a[f"Share_{cat}"] = round(shares[cat], 6)
        row_a["Shannon_Entropy_H"] = round(entropy, 6)
        rows_A.append(row_a)

                                                                                
        row_b = {"Province": prov_en, "Province_CN": prov, "Year": yr,
                 "Total_Supply_Flow_Mtce": round(total_supply, 2),
                 "Trans_Total_Mtce": round(trans_total, 2),
                 "Trans_Ratio_tau": round(trans_ratio, 6),
                 "Direct_Ratio": round(max(0, 1 - trans_ratio), 6)}
        for k, v2 in tflow.items():
            row_b[f"AbsFlow_{k}_Mtce"] = round(v2, 2)
            row_b[f"Share_{k}"]        = round(v2 / total_supply if total_supply > 0 else 0, 6)
        rows_B.append(row_b)

                                                                                
        row_c = {"Province": prov_en, "Province_CN": prov, "Year": yr,
                 "Shannon_Entropy_H": round(entropy, 6),
                 "HHI": round(hhi, 6),
                 "N_Active_Supply_Sources": n_active,
                 "Trans_Ratio_tau": round(trans_ratio, 6)}
        for sn, sen in SUPPLY_EN.items():
            abs_flow = supply_src.get(sn, 0)
            row_c[f"AbsFlow_{sen}_Mtce"] = round(abs_flow, 2)
            row_c[f"Share_{sen}"]        = round(abs_flow / total_s if total_s > 0 else 0, 6)
        rows_C.append(row_c)

df_A = pd.DataFrame(rows_A)
df_B = pd.DataFrame(rows_B)
df_C = pd.DataFrame(rows_C)

df_A.to_csv(os.path.join(OUT, "data_A_energy_composition.csv"),       index=False, encoding="utf-8-sig")
df_B.to_csv(os.path.join(OUT, "transformation_dependency.csv"), index=False, encoding="utf-8-sig")
df_C.to_csv(os.path.join(OUT, "data_C_structural_trajectory.csv"),     index=False, encoding="utf-8-sig")
print(f"\nCSVs saved to: {OUT}")

                                                                            
print(f"\n=== Summary ===")
print(f"Total records: {len(df_A)} (30 provinces x 20 years = 600 expected)")
print(f"Unique provinces: {df_A['Province'].nunique()} (should be 30)")
print(f"Year range: {df_A['Year'].min()} - {df_A['Year'].max()}")

print("\n=== Plot C: all provinces summary (2020) ===")
key_2020 = df_C[df_C["Year"]==2020][
    ["Province","Shannon_Entropy_H","HHI","N_Active_Supply_Sources","Trans_Ratio_tau"]
].sort_values("Province").round(4)
print(key_2020.to_string(index=False))
