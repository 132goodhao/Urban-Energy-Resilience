"""Plot temporal and regional resilience summaries."""

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
    GRID_COVERAGE, GRID_NAME_MAP, GRID_COLORS_EN, FYP_COLORS,
    PROVINCE_NAME_MAP, NATURE_WIDTHS,
)

             
PROJECT = str(PROJECT_ROOT)
DATA_FILE = os.path.join(
    PROJECT, 'data', 'model_outputs',
    'tier3_structural', 'results',
    'structural_resilience_summary.xlsx',
)
OUTPUT_DIR = os.path.join(PROJECT, 'outputs', 'outputs', 'figures')

             
FYP_PERIODS = {
    '10th': (2001, 2005),
    '11th': (2006, 2010),
    '12th': (2011, 2015),
    '13th': (2016, 2020),
}

                                     
EN_TO_CN = {v: k for k, v in PROVINCE_NAME_MAP.items()}

def load_tier3():
    df = pd.read_excel(DATA_FILE)
                                                            
    df = df.set_index('region')
                                             
    year_cols = [c for c in df.columns if str(c).isdigit()]
    years = sorted([int(y) for y in year_cols])
    rename_map = {c: int(c) for c in year_cols}
    df = df.rename(columns=rename_map)
    return df, years

                                         
                                       
                                         
def plot_fig3b():
    df, years = load_tier3()
    apply_style('medium')
    fig, ax = plt.subplots(figsize=get_figsize(NATURE_WIDTHS['double'], 8))

    means = df[years].mean(axis=0)
    stds = df[years].std(axis=0)

                                                          
    ax.fill_between(years, means - stds, means + stds, alpha=0.2, color='#4A90D9')
    ax.plot(years, means, '-o', color='#4A90D9', linewidth=1.5, markersize=3,
            markeredgecolor='white', markeredgewidth=0.3, zorder=5)

                 
    max_yr = means.idxmax()
    min_yr = means.idxmin()
    ax.annotate(f'Peak: {means[max_yr]:.3f} ({max_yr})',
                xy=(max_yr, means[max_yr]),
                xytext=(max_yr + 1.5, means[max_yr] + 0.008),
                fontsize=6, arrowprops=dict(arrowstyle='->', lw=0.5, color='grey'),
                color='#2C3E50')
    ax.annotate(f'Trough: {means[min_yr]:.3f} ({min_yr})',
                xy=(min_yr, means[min_yr]),
                xytext=(min_yr - 3, means[min_yr] - 0.012),
                fontsize=6, arrowprops=dict(arrowstyle='->', lw=0.5, color='grey'),
                color='#2C3E50')

    ax.set_xlabel('Year')
    ax.set_ylabel('Structural resilience (national mean ± s.d.)')
    ax.set_xlim(2000.5, 2020.5)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], rotation=45, ha='right')
    setup_minor_ticks(ax, 'y')

                          
    for label, (start, end) in FYP_PERIODS.items():
        ax.axvspan(start - 0.5, end + 0.5, alpha=0.08,
                   color=FYP_COLORS[label], zorder=0)
        mid = (start + end) / 2
        ax.text(mid, ax.get_ylim()[1], f'{label} FYP',
                ha='center', va='bottom', fontsize=6,
                color=FYP_COLORS[label], fontweight='bold')

    fig.tight_layout()
    save_figure(fig, 'fig3b_national_temporal_evolution', OUTPUT_DIR)
    plt.close(fig)
    print('Fig. 3b done.')

                                         
                                           
                                         
def plot_fig3c():
    df, years = load_tier3()
    apply_style('small')
    fig, ax = plt.subplots(figsize=get_figsize(NATURE_WIDTHS['double'], 9))

    grid_names_en = list(GRID_COLORS_EN.keys())
    fyp_labels = list(FYP_PERIODS.keys())
    n_grids = len(grid_names_en)
    n_fyps = len(fyp_labels)
    bar_width = 0.18
    x = np.arange(n_grids)

    for j, fyp in enumerate(fyp_labels):
        start, end = FYP_PERIODS[fyp]
        fyp_years = [y for y in years if start <= y <= end]
        grid_means = []
        grid_stds = []
        for grid_cn, provinces_cn in GRID_COVERAGE.items():
                                                               
            provinces_en = [PROVINCE_NAME_MAP.get(p, p) for p in provinces_cn]
            mask = df.index.isin(provinces_en)
            vals = df.loc[mask, fyp_years].values.flatten()
            vals = vals[~np.isnan(vals)]
            grid_means.append(np.mean(vals) if len(vals) > 0 else 0)
            grid_stds.append(np.std(vals) if len(vals) > 0 else 0)

        offset = (j - (n_fyps - 1) / 2) * bar_width
        ax.bar(x + offset, grid_means, bar_width,
               yerr=grid_stds, capsize=2,
               color=FYP_COLORS[fyp], alpha=0.85,
               edgecolor='white', linewidth=0.3,
               label=f'{fyp} FYP', zorder=3,
               error_kw={'linewidth': 0.5})

    ax.set_xlabel('Regional power grid')
    ax.set_ylabel('Mean structural resilience')
    ax.set_xticks(x)
    ax.set_xticklabels(grid_names_en, rotation=30, ha='right')
    ax.legend(frameon=False, loc='upper right', ncol=2)
    setup_minor_ticks(ax, 'y')

    fig.tight_layout()
    save_figure(fig, 'fig3c_regional_grid_comparison', OUTPUT_DIR)
    plt.close(fig)
    print('Fig. 3c done.')

if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_fig3b()
    plot_fig3c()
