"""Run selected figure generation scripts."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

print('=' * 60)
print('PROJECT_ROOT Figure Generation — All Figures')
print('=' * 60)

                    
print('\n--- Fig. 3b & 3c: Temporal + Regional ---')
try:
    from plot_temporal_regional_resilience import plot_fig3b, plot_fig3c
    plot_fig3b()
    plot_fig3c()
except Exception as e:
    print(f'ERROR in Fig 3b/3c: {e}')

                    
print('\n--- Fig. 4a & 4b: Three-tier decomposition ---')
try:
    from plot_three_tier_resilience import load_data, plot_fig4a, plot_fig4b
    df = load_data()
    plot_fig4a(df)
    plot_fig4b(df)
except Exception as e:
    print(f'ERROR in Fig 4a/4b: {e}')

                    
print('\n--- Fig. 5a & 5b: Validation scatter plots ---')
try:
    from plot_validation_scatter import plot_fig5a, plot_fig5b
    plot_fig5a()
    plot_fig5b()
except Exception as e:
    print(f'ERROR in Fig 5a/5b: {e}')

              
print('\n--- Fig. 6: Resilience redistribution ---')
try:
    from plot_resilience_redistribution import plot_fig6
    plot_fig6()
except Exception as e:
    print(f'ERROR in Fig 6: {e}')

print('\n' + '=' * 60)
print('Figure generation complete.')
print('Output directory: ../outputs/figures/')
print('=' * 60)
