"""Plot a three-tier resilience radar chart."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import (
    apply_style, setup_minor_ticks, save_figure, get_figsize,
    PROVINCE_NAME_MAP, NATURE_WIDTHS,
)

PROJECT = str(PROJECT_ROOT)
MODEL_DIR = os.path.join(PROJECT, 'data', 'model_outputs')

TIER1_FILE = os.path.join(MODEL_DIR, 'tier1_economic_energy', 'economic_energy_resilience.xlsx')
TIER2_FILE = os.path.join(MODEL_DIR, 'tier2_demand_side', 'demand_side_resilience.xlsx')
TIER3_FILE = os.path.join(MODEL_DIR, 'tier3_structural', 'results',
                          'structural_resilience_summary.xlsx')
OUTPUT_DIR = os.path.join(PROJECT, 'outputs', 'outputs', 'figures', 'draft_figures')

                 
CN_TO_EN = PROVINCE_NAME_MAP
EN_TO_CN = {v: k for k, v in CN_TO_EN.items()}

def load_data():
                                                                               
    t1 = pd.read_excel(TIER1_FILE)
    t2 = pd.read_excel(TIER2_FILE)
    t1_year_cols = [c for c in t1.columns if isinstance(c, (int, float)) and c >= 2000]
    t2_year_cols = [c for c in t2.columns if isinstance(c, (int, float)) and c >= 2000]
    t1_avg = t1[t1_year_cols].mean(axis=1)
    t2_avg = t2[t2_year_cols].mean(axis=1)
                        
    t1_avg.index = t1_avg.index.map(lambda x: CN_TO_EN.get(x, x))
    t2_avg.index = t2_avg.index.map(lambda x: CN_TO_EN.get(x, x))

                                                                           
    t3 = pd.read_excel(TIER3_FILE)
    t3 = t3.set_index('region')
    t3_year_cols = [c for c in t3.columns if str(c).isdigit()]
    t3_avg = t3[t3_year_cols].astype(float).mean(axis=1)

                             
    def normalise(s):
        s = s.dropna()
        rng = s.max() - s.min()
        if rng == 0:
            return s * 0
        return (s - s.min()) / rng

                              
    common = t1_avg.index.intersection(t2_avg.index).intersection(t3_avg.index)
    df = pd.DataFrame({
        'Tier 1 (Economic)': normalise(t1_avg.loc[common]),
        'Tier 2 (Demand-side)': normalise(t2_avg.loc[common]),
        'Tier 3 (Structural)': normalise(t3_avg.loc[common]),
    })
    df['Province_EN'] = df.index
    return df

                                         
                                     
                                         
def plot_fig5a(df):
    apply_style('medium')

    case_provinces = ['Guangdong', 'Inner Mongolia', 'Liaoning', 'Qinghai']
    case_colors = ['#E74C3C', '#F39C12', '#3498DB', '#27AE60']
    tiers = ['Tier 1 (Economic)', 'Tier 2 (Demand-side)', 'Tier 3 (Structural)']
    n_tiers = len(tiers)

    angles = np.linspace(0, 2 * np.pi, n_tiers, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=get_figsize(12, 12), subplot_kw=dict(polar=True))

    for prov, color in zip(case_provinces, case_colors):
        if prov in df.index:
            values = df.loc[prov, tiers].values.tolist()
            values += values[:1]
            ax.plot(angles, values, 'o-', linewidth=1.2, markersize=4,
                    color=color, label=prov, zorder=5)
            ax.fill(angles, values, alpha=0.08, color=color)

                    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(['Economic-energy\nresilience', 'Social-energy\nresilience',
                        'Structural-energy\nresilience'], fontsize=7)
    ax.set_ylim(0, 1.1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=5)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), frameon=False)

    fig.tight_layout()
    save_figure(fig, 'fig5a_radar_provinces', OUTPUT_DIR)
    plt.close(fig)
    print('Fig. 5a done.')

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)
    
    df = load_data()
    
                                                                 
    case_provinces = ['Guangdong', 'Inner Mongolia', 'Liaoning', 'Qinghai']
    tiers = ['Tier 1 (Economic)', 'Tier 2 (Demand-side)', 'Tier 3 (Structural)']
    
                                                              
    export_df = df.loc[case_provinces, tiers].copy()
    export_df.columns = ['Economic-energy resilience', 'Social-energy resilience', 'Structural-energy resilience']
    export_df.index.name = 'Province'
    
                   
    output_file = os.path.join(DATA_OUTPUT_DIR, 'fig5a_radar_chart_data.xlsx')
    export_df.to_excel(output_file)
    print(f'Data exported to: {output_file}')
    
    plot_fig5a(df)
