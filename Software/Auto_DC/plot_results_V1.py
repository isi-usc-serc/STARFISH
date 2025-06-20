# -*- coding: utf-8 -*-
"""
SMA Characterization Plotting

This script will read the data from the Auto_DC program and plot the results.

Created on Tue Jun 17 16:14:19 2025

@author: Billy Christ
"""

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba
from scipy.interpolate import griddata
from collections import defaultdict

# Path to data directory
DATA_DIR = r"C:\Users\Owner\Desktop\SERC\STARFISH_Project\Software\STARFISH\Thermo_Position_Data"

# Find all run CSV files
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*V_*A_*G_run_*.csv")))
print(f"[DEBUG] Found {len(csv_files)} CSV files")

def format_setup_title(prefix):
    """Format setup parameters for readable titles (replace 'p' with '.')"""
    formatted = prefix.replace('p', '.')
    formatted = formatted.replace('_', ', ')
    return formatted

groups = defaultdict(list)
for path in csv_files:
    fname = os.path.basename(path)
    prefix = fname.split("_run_")[0]
    groups[prefix].append(path)

print(f"[DEBUG] Grouped into {len(groups)} setups")

# Define base colors for different trials
base_colors = [
    'blue', 'orange', 'green', 'purple', 'cyan',
    'magenta', 'brown', 'olive', 'teal', 'pink'
]

for prefix, files in groups.items():
    print(f"[DEBUG] Processing setup: {prefix} with {len(files)} files")
    all_displacement = []
    all_temp = []
    all_trial = []
    all_sma = []
    all_titles = []

    for csv_path in files:
        fname = os.path.basename(csv_path)
        # Extract actual run number from filename
        try:
            run_part = fname.split("_run_")[-1]
            run_idx = int(run_part.split(".")[0])
        except ValueError:
            print(f"[WARN] Could not parse run number from {fname}, skipping.")
            continue

        df = pd.read_csv(csv_path)
        print(f"[DEBUG] File {run_idx}: {len(df)} rows")

        required_cols = ["x_mm", "y_mm", "temp_ch0", "sma_active"]
        if not all(col in df.columns for col in required_cols):
            print(f"[WARN] Missing columns in {csv_path}, skipping.")
            continue
        if df.empty:
            print(f"[WARN] {csv_path} is empty, skipping.")
            continue

        df = df[pd.to_numeric(df["temp_ch0"], errors="coerce").notnull()]
        if df.empty:
            print(f"[WARN] All temperature values invalid in {csv_path}, skipping.")
            continue

        title = f"SMA Characterization for {format_setup_title(prefix)}"
        all_titles.append(title)
        first_row = df.iloc[0]
        x0, y0 = first_row["x_mm"], first_row["y_mm"]
        displacement = np.sqrt((df["x_mm"] - x0) ** 2 + (df["y_mm"] - y0) ** 2)
        temp = df["temp_ch0"]
        trial = np.full(displacement.shape, run_idx, dtype=int)
        sma = df["sma_active"].astype(bool)

        all_displacement.append(displacement)
        all_temp.append(temp)
        all_trial.append(trial)
        all_sma.append(sma)

    if all_displacement:
        print(f"[DEBUG] Creating plots for {len(all_displacement)} trials")
        disp = np.concatenate(all_displacement)
        temp = np.concatenate(all_temp)
        trial = np.concatenate(all_trial)
        sma = np.concatenate(all_sma)

        # 3D Scatter plot
        fig = plt.figure(figsize=(12, 7))
        ax = fig.add_subplot(111, projection='3d')
        for c in [True, False]:
            mask = sma == c
            ax.scatter(disp[mask], trial[mask], temp[mask],
                       c='red' if c else 'blue', label='SMA ON' if c else 'SMA OFF', marker='o', alpha=0.7)

        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        zlim = ax.get_zlim()
        y_center = (ylim[0] + ylim[1]) / 2
        y_range = (ylim[1] - ylim[0])
        stretch = 2.0
        new_ylim = (y_center - (y_range * stretch) / 2, y_center + (y_range * stretch) / 2)
        ax.set_ylim(new_ylim)

        ax.set_xlabel('Displacement [mm]')
        ax.set_ylabel('Trial Number')
        ax.set_zlabel('Temperature [°C]')
        plt.title(all_titles[0] if all_titles else 'SMA Characterization')
        ax.legend()
        plt.tight_layout()
        plt.show()

        # 2D plots for each trial
        print(f"[DEBUG] Creating 2D plots for {len(np.unique(trial))} trials...")
        for run_idx in np.unique(trial):
            trial_mask = trial == run_idx
            if np.any(trial_mask):
                trial_disp = disp[trial_mask]
                trial_temp = temp[trial_mask]
                trial_sma = sma[trial_mask]

                fig, ax = plt.subplots(figsize=(8, 5))
                ax.scatter(trial_disp[trial_sma], trial_temp[trial_sma], color='red', label='SMA ON', alpha=0.7)
                ax.scatter(trial_disp[~trial_sma], trial_temp[~trial_sma], color='blue', label='SMA OFF', alpha=0.7)
                ax.set_xlabel('Displacement [mm]')
                ax.set_ylabel('Temperature [°C]')
                ax.set_title(f'{format_setup_title(prefix)} Run {run_idx}')
                ax.legend()
                fig.tight_layout()
                plt.show()

        # Combined overlay plot
        print(f"[DEBUG] Creating combined overlay plot for setup: {prefix}")
        fig, ax = plt.subplots(figsize=(10, 6))
        trial_ids = sorted(np.unique(trial))

        for i, run_idx in enumerate(trial_ids):
            trial_mask = trial == run_idx
            trial_disp = disp[trial_mask]
            trial_temp = temp[trial_mask]
            trial_sma = sma[trial_mask]
            base = base_colors[i % len(base_colors)]
            on_color = to_rgba(base, alpha=0.9)
            off_color = to_rgba(base, alpha=0.4)

            on_mask = trial_sma
            off_mask = ~trial_sma

            ax.scatter(trial_disp[on_mask], trial_temp[on_mask], color=on_color,
                       label=f'Trial {run_idx} SMA ON', alpha=0.8, marker='o')
            ax.scatter(trial_disp[off_mask], trial_temp[off_mask], color=off_color,
                       label=f'Trial {run_idx} SMA OFF', alpha=0.6, marker='x')

        ax.set_xlabel('Displacement [mm]')
        ax.set_ylabel('Temperature [°C]')
        ax.set_title(f'{format_setup_title(prefix)} - All Runs')
        ax.legend(fontsize='small', loc='upper left', bbox_to_anchor=(1, 1))
        fig.tight_layout()
        plt.show()

        # Surface plots for each trial
        print(f"[DEBUG] Creating surface plots for {len(np.unique(trial))} trials...")
        for run_idx in np.unique(trial):
            trial_mask = trial == run_idx
            if np.any(trial_mask):
                trial_disp = disp[trial_mask]
                trial_temp = temp[trial_mask]
                trial_sma = sma[trial_mask]
                print(f"[DEBUG] Creating surface plot for trial {run_idx} with {len(trial_disp)} points")

                trial_time = np.linspace(0, len(trial_disp)-1, len(trial_disp))

                # Grid and interpolation with NaN check
                valid_mask = ~np.isnan(trial_disp) & ~np.isnan(trial_temp) & ~np.isnan(trial_time)
                if not np.any(valid_mask):
                    print(f"[WARN] Trial {run_idx} contains only NaNs, skipping surface plot.")
                    continue

                points = np.column_stack((trial_disp[valid_mask], trial_time[valid_mask]))
                values = trial_temp[valid_mask]
                xi = np.linspace(np.min(trial_disp[valid_mask]), np.max(trial_disp[valid_mask]), 50)
                yi = np.linspace(np.min(trial_time[valid_mask]), np.max(trial_time[valid_mask]), 50)
                xi_grid, yi_grid = np.meshgrid(xi, yi)
                zi_grid = griddata(points, values, (xi_grid, yi_grid), method='linear')

                # (Surface plot disabled, but data now prepared safely)
    else:
        print(f"[ERROR] No valid data found to plot for {prefix}.")

print("Plotting complete!")
