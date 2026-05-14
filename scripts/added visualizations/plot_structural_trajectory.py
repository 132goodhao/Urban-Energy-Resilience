"""Plot structural trajectory metrics."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

       
PROJECT = r"data/model_outputs"
PKL = os.path.join(PROJECT, "networks", "provincial_energy_networks.pkl")
OUT_PLOT = r"outputs\outputs/figures\draft_figures"

                                
os.makedirs(OUT_PLOT, exist_ok=True)

                   
print("Loading network data...")
with open(PKL, "rb") as f:
    all_networks = pickle.load(f)
print("Loaded.")

           
GRID = {"Liaoning": "Northeast grid", "Qinghai": "Northwest grid"}
PROVINCES = ["Liaoning", "Qinghai"]
ALL_YEARS = list(range(2001, 2021))
YEARS = [2001, 2010, 2020]
LN_C = "#C0392B"
QH_C = "#2471A3"

               
energy_categories = {
}
supply_nodes = {
}
transformation_nodes = {
}
all_carriers = [item for items in energy_categories.values() for item in items]

                 
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
    shares = {cat: (cat_flow[cat]/total_supply_flow if total_supply_flow > 0 else 0)
              for cat in energy_categories}
    entropy = -sum(s*math.log(s) for s in shares.values() if s > 0)

    supply_src = {}
    for u, v, d in G.edges(data=True):
        if u in supply_nodes:
            supply_src[u] = supply_src.get(u, 0) + abs(d.get("weight", 0))
    total_s = sum(supply_src.values())
    hhi = sum((v/total_s)**2 for v in supply_src.values()) if total_s > 0 else 1.0

    return shares, entropy, hhi

import math

print("Computing structural metrics for all years...")
records = {}
for prov in PROVINCES:
    grid = GRID[prov]
    records[prov] = {"entropy": [], "hhi": [], "shares": []}
    for yr in ALL_YEARS:
        G = all_networks[grid][yr][prov]
        shares, ent, hhi = get_metrics(G)
        records[prov]["entropy"].append(ent)
        records[prov]["hhi"].append(hhi)
        records[prov]["shares"].append(shares)
print("Metrics done.")

             
fig, ax = plt.subplots(figsize=(7, 5.5))

for prov, color, label in [("Liaoning", LN_C, "Liaoning"), ("Qinghai", QH_C, "Qinghai")]:
    ent = records[prov]["entropy"]
    hhi = records[prov]["hhi"]

                    
    sc = ax.scatter(ent, hhi, c=ALL_YEARS, cmap="YlOrRd_r",
                    vmin=2001, vmax=2020, s=48, zorder=4,
                    edgecolors=color, linewidths=0.8)

                             
    ax.plot(ent, hhi, color=color, lw=1.2, alpha=0.5, zorder=2)

                 
    for yr in [2001, 2010, 2020]:
        idx = ALL_YEARS.index(yr)
        ax.text(ent[idx]+off_x, hhi[idx], str(yr),
                fontsize=8, color=color, ha=off_align, va="center", zorder=6)

                           
    ax.text(ent[-1], hhi[-1]+0.014, label,
            fontsize=10, color=color, fontweight="bold", ha="center", zorder=6)

                                      
xlim, ylim = ax.get_xlim(), ax.get_ylim()
cbar_ax = fig.add_axes([0.18, 0.72, 0.15, 0.03])
cbar = fig.colorbar(sc, cax=cbar_ax, orientation="horizontal")
cbar.set_ticks([2001, 2010, 2020])
cbar.ax.tick_params(labelsize=8)

             
ax.set_xlabel("Shannon Entropy", fontsize=11)
ax.set_ylabel("Herfindahl-Hirschman Index", fontsize=11)

out_path = os.path.join(OUT_PLOT, "fig4f_draft.png")
fig.savefig(out_path, dpi=300)
plt.close(fig)
print(f"Saved: {out_path}")
