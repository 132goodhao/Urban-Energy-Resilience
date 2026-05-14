"""Shared plotting style utilities."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.ticker import AutoMinorLocator

                       
def cm_to_inch(cm):
    return cm / 2.54

def get_figsize(width_cm, height_cm):
    return (cm_to_inch(width_cm), cm_to_inch(height_cm))

                                   
NATURE_WIDTHS = {
    'single': 8.9,
    'half': 9.0,
    'double': 18.3,
}

                    
FONT_CONFIGS = {
    'tiny': {
        'font.size': 6, 'axes.labelsize': 6, 'axes.titlesize': 7,
        'xtick.labelsize': 5, 'ytick.labelsize': 5, 'legend.fontsize': 5,
    },
    'small': {
        'font.size': 7, 'axes.labelsize': 7, 'axes.titlesize': 8,
        'xtick.labelsize': 6, 'ytick.labelsize': 6, 'legend.fontsize': 6,
    },
    'medium': {
        'font.size': 8, 'axes.labelsize': 8, 'axes.titlesize': 9,
        'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 7,
    },
    'regular': {
        'font.size': 9, 'axes.labelsize': 9, 'axes.titlesize': 10,
        'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
    },
}

                  
BASE_STYLE = {
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica'],
    'axes.linewidth': 0.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.minor.width': 0.3,
    'ytick.minor.width': 0.3,
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'xtick.major.size': 3,
    'ytick.major.size': 3,
    'xtick.minor.size': 1.5,
    'ytick.minor.size': 1.5,
    'figure.dpi': 150,
    'savefig.dpi': 1000,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.unicode_minus': False,
    'pdf.fonttype': 42,
    'ps.fonttype': 42,
}

                      
                                            
COLORS = {
    'primary': '#C65D57',
    'secondary': '#D4A373',
    'highlight': '#BC6C25',
    'neutral': ['#DDA15E', '#FEFAE0', '#BC6C25', '#606C38', '#283618'],
}

                                 
GRID_COLORS = {
}

GRID_COLORS_EN = {
    'North China': '#E74C3C',
    'Northeast': '#3498DB',
    'East China': '#2ECC71',
    'Central China': '#F39C12',
    'Northwest': '#9B59B6',
    'Southern': '#1ABC9C',
}

                    
FYP_COLORS = {
    '10th': '#4A90D9',
    '11th': '#2ECC71',
    '12th': '#F39C12',
    '13th': '#E74C3C',
}

                             
GRID_NAME_MAP = {
}

                                 
PROVINCE_NAME_MAP = {
}

                                   
GRID_COVERAGE = {
}

def apply_style(font_style='small'):
    plot_style = {**BASE_STYLE, **FONT_CONFIGS[font_style]}
    rcParams.update(plot_style)

def setup_minor_ticks(ax, axis='both'):
    if axis in ['x', 'both']:
        ax.xaxis.set_minor_locator(AutoMinorLocator())
    if axis in ['y', 'both']:
        ax.yaxis.set_minor_locator(AutoMinorLocator())

def save_figure(fig, name, output_dir='../outputs/figures'):
    import os
    os.makedirs(output_dir, exist_ok=True)
    for fmt in ['png', 'pdf', 'svg']:
        fig.savefig(
            os.path.join(output_dir, f'{name}.{fmt}'),
            format=fmt, dpi=1000, transparent=True,
            bbox_inches='tight', pad_inches=0.02,
        )
    print(f'Saved: {name}.png / .pdf / .svg')
