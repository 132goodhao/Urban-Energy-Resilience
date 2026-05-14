"""Plot redistribution scatter results."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import (
    apply_style, setup_minor_ticks, save_figure, get_figsize,
    PROVINCE_NAME_MAP, NATURE_WIDTHS,
)

PROJECT = str(PROJECT_ROOT)
MODEL_DIR = os.path.join(PROJECT, 'data', 'model_outputs')
VALIDATION_DIR = os.path.join(MODEL_DIR, 'validation')

TIER3_FILE = os.path.join(MODEL_DIR, 'tier3_structural', 'results',
                          'structural_resilience_summary.xlsx')
OUTFLOW_FILE = os.path.join(VALIDATION_DIR, 'interprovincial_energy_outflow.xlsx')
INFLOW_FILE = os.path.join(VALIDATION_DIR, 'interprovincial_energy_inflow.xlsx')
OUTPUT_DIR = os.path.join(PROJECT, 'outputs', 'outputs', 'figures', 'draft_figures')

CN_TO_EN = PROVINCE_NAME_MAP
EN_TO_CN = {v: k for k, v in CN_TO_EN.items()}

def plot_fig5b():
    apply_style('medium')

                                                              
    t3 = pd.read_excel(TIER3_FILE)
    t3 = t3.set_index('region')
    year_cols = [c for c in t3.columns if str(c).isdigit()]
                        
    for c in year_cols:
        t3[c] = pd.to_numeric(t3[c], errors='coerce')

    fyp10_cols = [c for c in year_cols if 2001 <= int(c) <= 2005]
    fyp13_cols = [c for c in year_cols if 2016 <= int(c) <= 2020]
    resilience_change = t3[fyp13_cols].mean(axis=1) - t3[fyp10_cols].mean(axis=1)

                                                                                      
    outflow = pd.read_excel(OUTFLOW_FILE, index_col=0)
    inflow = pd.read_excel(INFLOW_FILE, index_col=0)

                                                             
    out_year_cols = [c for c in outflow.columns if str(c).isdigit()]
    in_year_cols = [c for c in inflow.columns if str(c).isdigit()]

    for c in out_year_cols:
        outflow[c] = pd.to_numeric(outflow[c], errors='coerce')
    for c in in_year_cols:
        inflow[c] = pd.to_numeric(inflow[c], errors='coerce')

    net_export_cn = outflow[out_year_cols].mean(axis=1) - inflow[in_year_cols].mean(axis=1)

                                                  
    net_export = net_export_cn.copy()
    net_export.index = net_export.index.map(lambda x: CN_TO_EN.get(x, x))

                         
    common = resilience_change.index.intersection(net_export.index)
    print(f'Common provinces: {len(common)}')

    if len(common) == 0:
        print('ERROR: No common provinces found. Check name mapping.')
        return
    
                                           
    export_df = pd.DataFrame({
        'Province': common,
        'Net energy export (10,000 tce)': [net_export[prov] for prov in common],
        'Resilience change (13th FYP - 10th FYP)': [resilience_change[prov] for prov in common],
        'Category': ['Net exporter' if net_export[prov] > 0 else 'Net importer' for prov in common]
    })
    export_df = export_df.set_index('Province')
    
                   
    os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)
    output_file = os.path.join(DATA_OUTPUT_DIR, 'fig5b_scatter_plot_data.xlsx')
    export_df.to_excel(output_file)
    print(f'Data exported to: {output_file}')

                                           
    fig, ax = plt.subplots(figsize=get_figsize(10, 8))

    for prov in common:
        ne = net_export[prov]
        rc = resilience_change[prov]

        if pd.isna(ne) or pd.isna(rc):
            continue

                                                           
        color = '#E74C3C' if ne > 0 else '#3498DB'
                                      
        size = min(max(abs(ne) / 300, 20), 250) * 1.2

                                                                 
        ax.scatter(ne, rc, s=size, c=color, alpha=0.5,
                   edgecolors='white', linewidth=0.3, zorder=5)
        ax.annotate(prov, (ne, rc), fontsize=4.5, alpha=0.7,
                    xytext=(3, 3), textcoords='offset points')

                     
    ax.axhline(0, color='grey', linewidth=0.5, linestyle='--', alpha=0.5, zorder=1)
    ax.axvline(0, color='grey', linewidth=0.5, linestyle='--', alpha=0.5, zorder=1)

                     
    ax.text(0.95, 0.95, 'Net exporter +\nResilience improved',
            transform=ax.transAxes, ha='right', va='top', fontsize=5,
            color='#27AE60', alpha=0.5)
    ax.text(0.95, 0.05, 'Net exporter +\nResilience declined',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=5,
            color='#E74C3C', alpha=0.5)
    ax.text(0.05, 0.95, 'Net importer +\nResilience improved',
            transform=ax.transAxes, ha='left', va='top', fontsize=5,
            color='#27AE60', alpha=0.5)
    ax.text(0.05, 0.05, 'Net importer +\nResilience declined',
            transform=ax.transAxes, ha='left', va='bottom', fontsize=5,
            color='#E74C3C', alpha=0.5)

                                                        
    legend_elements = [
        mpatches.Patch(color='#E74C3C', alpha=0.5, label='Net energy exporter'),
        mpatches.Patch(color='#3498DB', alpha=0.5, label='Net energy importer'),
    ]
    ax.legend(handles=legend_elements, frameon=False, loc='lower right')

    ax.set_xlabel('Net energy export (20-year average, 10,000 tce)')
    ax.set_ylabel('Change in structural resilience\n(13th FYP mean \u2212 10th FYP mean)')
    setup_minor_ticks(ax)

    fig.tight_layout()
    save_figure(fig, 'fig5b_resilience_redistribution', OUTPUT_DIR)
    plt.close(fig)
    print('Fig. 5b done.')

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_fig5b()
