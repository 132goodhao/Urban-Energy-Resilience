"""Plot transformation dependency results."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit

       
RESILIENCE_FILE = r"data/model_outputs\tier3_structural\results\structural_resilience_summary.xlsx"
TRANS_RATIO_CSV = r"outputs\tables\figure_data\transformation_dependency.csv"
OUT_EXCEL = r"outputs\tables\figure_data\transformation_dependency_data.xlsx"
OUT_FIG = r"outputs\outputs/figures\draft_figures\fig4e.png"

os.makedirs(os.path.dirname(OUT_EXCEL), exist_ok=True)
os.makedirs(os.path.dirname(OUT_FIG), exist_ok=True)

           
df_resilience = pd.read_excel(RESILIENCE_FILE, sheet_name=0)
df_trans = pd.read_csv(TRANS_RATIO_CSV)

                                                   
trans_pivot = df_trans.pivot(index='Province', columns='Year', values='Trans_Ratio_tau').reset_index()
year_cols = [str(y) for y in range(2001, 2021)]
trans_pivot.columns = ['Province'] + year_cols

                    
trans_pivot['average'] = trans_pivot[year_cols].mean(axis=1)

                                               
grid_region = df_resilience[['region', 'grid_name']].copy()
grid_region['Province'] = df_resilience['region']
trans_pivot = trans_pivot.merge(grid_region[['Province', 'grid_name', 'region']], on='Province', how='left')

                                            
trans_pivot = trans_pivot[['grid_name', 'region'] + year_cols + ['average']]

             
with pd.ExcelWriter(OUT_EXCEL, engine='openpyxl') as writer:
    df_resilience.to_excel(writer, sheet_name='Resilience', index=False)
    trans_pivot.to_excel(writer, sheet_name='Trans_Ratio', index=False)
print(f"Excel saved: {OUT_EXCEL}")

                                                    
merge_data = df_resilience[['region', 'average']].merge(
    trans_pivot[['region', 'average']], on='region', suffixes=('_resilience', '_trans')
).dropna()

x = merge_data['average_trans'].values
y = merge_data['average_resilience'].values

                   
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
r_squared = r_value ** 2

                      
x_fit = np.linspace(x.min() * 0.9, x.max() * 1.1, 100)
y_fit = slope * x_fit + intercept

                                 
n = len(x)
x_mean = np.mean(x)
t_val = stats.t.ppf(0.975, n - 2)          
residuals = y - (slope * x + intercept)
mse = np.sum(residuals**2) / (n - 2)
se_fit = np.sqrt(mse * (1/n + (x_fit - x_mean)**2 / np.sum((x - x_mean)**2)))
ci = t_val * se_fit

             
fig, ax = plt.subplots(figsize=(8, 6))

                
ax.scatter(x, y, c='steelblue', s=80, alpha=0.7, edgecolors='black', linewidth=0.5, zorder=3)

             
ax.plot(x_fit, y_fit, 'r-', linewidth=2, zorder=4, label=f'Linear fit: y={slope:.3f}x+{intercept:.3f}')

                     
ax.fill_between(x_fit, y_fit - ci, y_fit + ci, color='red', alpha=0.2, zorder=2)

                  
ax.set_xlabel('Trans_Ratio ($\\tau$)', fontsize=14, fontweight='bold')
ax.set_ylabel('Topological-energy Resilience', fontsize=14, fontweight='bold')
ax.set_title('Relationship between Transformation Dependency and Resilience', fontsize=12)

            
stats_text = f'$r$ = {r_value:.3f}\n$p$ = {p_value:.4f}\n$R^2$ = {r_squared:.3f}'
ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

                  
ax.grid(True, linestyle='--', alpha=0.3)
ax.set_xlim(0, 1.1)
ax.set_ylim(0, 0.4)

plt.tight_layout()
plt.savefig(OUT_FIG, dpi=300, bbox_inches='tight')
print(f"Figure saved: {OUT_FIG}")

               
print(f"\n=== Summary ===")
print(f"N provinces: {len(merge_data)}")
print(f"r = {r_value:.4f}")
print(f"p = {p_value:.4f}")
print(f"R² = {r_squared:.4f}")
