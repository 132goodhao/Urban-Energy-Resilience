"""Plot validation scatter charts."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_style import (
    apply_style, setup_minor_ticks, save_figure, get_figsize,
    GRID_COVERAGE, GRID_NAME_MAP, GRID_COLORS_EN,
    PROVINCE_NAME_MAP, NATURE_WIDTHS,
)

PROJECT = str(PROJECT_ROOT)
MODEL_DIR = os.path.join(PROJECT, 'data', 'model_outputs')
TIER3_FILE = os.path.join(MODEL_DIR, 'tier3_structural', 'results',
                          'structural_resilience_summary.xlsx')
VALIDATION_DIR = os.path.join(MODEL_DIR, 'validation')
OUTPUT_DIR = os.path.join(PROJECT, 'outputs', 'outputs', 'figures')

CN_TO_EN = PROVINCE_NAME_MAP
EN_TO_CN = {v: k for k, v in CN_TO_EN.items()}

def get_grid_color_en(province_en):
    province_cn = EN_TO_CN.get(province_en, province_en)
    for grid_cn, provinces in GRID_COVERAGE.items():
        if province_cn in provinces:
            en = GRID_NAME_MAP[grid_cn]
            return en, GRID_COLORS_EN[en]
    return 'Unknown', '#999999'

def load_tier3_avg():
    df = pd.read_excel(TIER3_FILE)
    df = df.set_index('region')
    year_cols = [c for c in df.columns if str(c).isdigit()]
    return df[year_cols].astype(float).mean(axis=1)

                                         
                              
                                         
def plot_fig5a():
    apply_style('medium')
    t3_avg = load_tier3_avg()

                                                                                  
    sma_file = os.path.join(VALIDATION_DIR, 'df_all_sma.xlsx')
    if os.path.exists(sma_file):
        sma_df = pd.read_excel(sma_file)
        print(f'Loaded df_all_sma.xlsx: columns = {list(sma_df.columns[:8])}')
        print(f'Shape: {sma_df.shape}')
                                                
        if 'HHI' in sma_df.columns or 'hhi' in [c.lower() for c in sma_df.columns]:
                                
            hhi_col = [c for c in sma_df.columns if 'hhi' in c.lower()][0]
                                          
            pass

                                                                                   
    sma_out_file = os.path.join(VALIDATION_DIR, 'sma_out.xlsx')
    dep_file = os.path.join(VALIDATION_DIR, 'Standardized_Importance.xlsx')

                                                                                 
    if os.path.exists(dep_file):
        dep_df = pd.read_excel(dep_file, index_col=0)
        print(f'Loaded Standardized_Importance: index = {list(dep_df.index[:5])}')
        dep_avg = dep_df.select_dtypes(include=[np.number]).mean(axis=1)
                             
        if dep_avg.index[0] in CN_TO_EN:
            dep_avg.index = dep_avg.index.map(lambda x: CN_TO_EN.get(x, x))

        common = t3_avg.index.intersection(dep_avg.index)
        if len(common) > 5:
            fig, ax = plt.subplots(figsize=get_figsize(NATURE_WIDTHS['half'], 9))
            for prov in common:
                grid_en, color = get_grid_color_en(prov)
                ax.scatter(dep_avg[prov], t3_avg[prov], c=color, s=30, alpha=0.7,
                           edgecolors='white', linewidth=0.3, zorder=5)
                ax.annotate(prov, (dep_avg[prov], t3_avg[prov]),
                            fontsize=4, alpha=0.6, xytext=(2, 2),
                            textcoords='offset points')

                        
            x_vals = dep_avg[common].values.astype(float)
            y_vals = t3_avg[common].values.astype(float)
            mask = ~(np.isnan(x_vals) | np.isnan(y_vals))
            if mask.sum() > 2:
                slope, intercept, r_val, p_val, _ = stats.linregress(x_vals[mask], y_vals[mask])
                x_line = np.linspace(x_vals[mask].min(), x_vals[mask].max(), 100)
                ax.plot(x_line, slope * x_line + intercept, '--', color='grey',
                        linewidth=0.8, alpha=0.7, zorder=3)
                ax.text(0.05, 0.95, f'r = {r_val:.3f}, p = {p_val:.3f}',
                        transform=ax.transAxes, fontsize=6, va='top',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                  edgecolor='grey', alpha=0.8))

            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor=c,
                       markersize=5, label=name)
                for name, c in GRID_COLORS_EN.items()
            ]
            ax.legend(handles=legend_elements, frameon=False, fontsize=5, loc='lower left')
            ax.set_xlabel('Standardised energy dependency importance')
            ax.set_ylabel('Structural resilience')
            setup_minor_ticks(ax)
            fig.tight_layout()
            save_figure(fig, 'fig5a_resilience_vs_dependency', OUTPUT_DIR)
            plt.close(fig)
            print('Fig. 5a done.')
            return

    print('WARNING: Could not find suitable validation data for Fig. 5a. Skipping.')

                                         
                                          
                                         
def plot_fig5b():
    apply_style('medium')
    t3_avg = load_tier3_avg()

                        
    disaster_file = os.path.join(VALIDATION_DIR, 'restructured_disaster_loss_data_filtered.xlsx')
    if not os.path.exists(disaster_file):
        print('WARNING: Disaster file not found. Skipping Fig. 5b.')
        return

    disaster = pd.read_excel(disaster_file, index_col=0)
                                     
    d_year_cols = [c for c in disaster.columns if isinstance(c, (int, float)) and c >= 2000]
    if len(d_year_cols) == 0:
        d_year_cols = [c for c in disaster.columns if str(c).isdigit()]
        disaster = disaster.rename(columns={c: int(c) for c in d_year_cols})
        d_year_cols = [int(c) for c in d_year_cols]

    disaster_avg = disaster[d_year_cols].mean(axis=1)
                                
    sample_idx = str(disaster_avg.index[0])
    if sample_idx in CN_TO_EN:
        disaster_avg.index = disaster_avg.index.map(lambda x: CN_TO_EN.get(x, x))

    common = t3_avg.index.intersection(disaster_avg.index)
    if len(common) < 3:
        print(f'Only {len(common)} common provinces. Skipping Fig. 5b.')
        return

    fig, ax = plt.subplots(figsize=get_figsize(NATURE_WIDTHS['half'], 9))

    for prov in common:
        grid_en, color = get_grid_color_en(prov)
        ax.scatter(t3_avg[prov], disaster_avg[prov], c=color, s=30, alpha=0.7,
                   edgecolors='white', linewidth=0.3, zorder=5)
        ax.annotate(prov, (t3_avg[prov], disaster_avg[prov]),
                    fontsize=4, alpha=0.6, xytext=(2, 2),
                    textcoords='offset points')

                
    x_vals = t3_avg[common].values.astype(float)
    y_vals = disaster_avg[common].values.astype(float)
    mask = ~(np.isnan(x_vals) | np.isnan(y_vals))
    if mask.sum() > 2:
        slope, intercept, r_val, p_val, _ = stats.linregress(x_vals[mask], y_vals[mask])
        x_line = np.linspace(x_vals[mask].min(), x_vals[mask].max(), 100)
        ax.plot(x_line, slope * x_line + intercept, '--', color='grey',
                linewidth=0.8, alpha=0.7, zorder=3)
        ax.text(0.05, 0.95, f'r = {r_val:.3f}, p = {p_val:.3f}',
                transform=ax.transAxes, fontsize=6, va='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                          edgecolor='grey', alpha=0.8))

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=c,
               markersize=5, label=name)
        for name, c in GRID_COLORS_EN.items()
    ]
    ax.legend(handles=legend_elements, frameon=False, fontsize=5, loc='upper right')
    ax.set_xlabel('Structural resilience')
    ax.set_ylabel('Disaster economic losses (100M RMB)')
    setup_minor_ticks(ax)

    fig.tight_layout()
    save_figure(fig, 'fig5b_resilience_vs_disaster', OUTPUT_DIR)
    plt.close(fig)
    print('Fig. 5b done.')

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_fig5a()
    plot_fig5b()
