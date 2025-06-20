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
from scipy.interpolate import griddata
from collections import defaultdict

# Path to data directory
DATA_DIR = r"C:\Users\Owner\Desktop\SERC\STARFISH_Project\Software\STARFISH\Thermo_Position_Data"

# Find all run CSV files
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*V_*A_*G_run_*.csv")))
print(f"[DEBUG] Found {len(csv_files)} CSV files")

def format_setup_title(prefix):
    """Format setup parameters for readable titles (replace 'p' with '.')"""
    # Replace 'p' with '.' for voltage and current values
    formatted = prefix.replace('p', '.')
    # Replace underscores with commas and spaces for better readability
    formatted = formatted.replace('_', ', ')
    return formatted

groups = defaultdict(list)
for path in csv_files:
    fname = os.path.basename(path)
    prefix = fname.split("_run_")[0]
    groups[prefix].append(path)

print(f"[DEBUG] Grouped into {len(groups)} setups")

for prefix, files in groups.items():
    print(f"[DEBUG] Processing setup: {prefix} with {len(files)} files")
    all_displacement = []
    all_temp = []
    all_trial = []
    all_sma = []
    all_titles = []
    
    for run_idx, csv_path in enumerate(files, 1):
        df = pd.read_csv(csv_path)
        print(f"[DEBUG] File {run_idx}: {len(df)} rows")
        required_cols = ["x_mm", "y_mm", "temp_ch0", "sma_active"]
        if not all(col in df.columns for col in required_cols):
            print(f"[WARN] Missing columns in {csv_path}, skipping.")
            continue
        if df.empty:
            print(f"[WARN] {csv_path} is empty, skipping.")
            continue
        # Filter out rows where temp_ch0 is None, NaN, or not a valid number
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
        colors = np.where(sma, 'red', 'blue')

        # Original 3D scatter plot
        fig = plt.figure(figsize=(12, 7))
        ax = fig.add_subplot(111, projection='3d')
        
        # Plot scatter points
        for c in [True, False]:
            mask = sma == c
            ax.scatter(disp[mask], trial[mask], temp[mask],
                       c='red' if c else 'blue', label='SMA ON' if c else 'SMA OFF', marker='o', alpha=0.7)
        
        # Remove connecting lines section
        # (No lines between points)

        # Adjust aspect ratio: make 'Trial Number' axis longer
        # This is done by setting the limits so the y-axis (trial) is visually longer
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        zlim = ax.get_zlim()
        # Stretch the y-axis (trial) by a factor, e.g., 2x
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
        
        # 2D plots for each trial: Temperature vs Displacement
        print(f"[DEBUG] Creating 2D plots for {len(files)} trials...")
        for run_idx in range(1, len(files) + 1):
            trial_mask = trial == run_idx
            if np.any(trial_mask):
                trial_disp = disp[trial_mask]
                trial_temp = temp[trial_mask]
                trial_sma = sma[trial_mask]

                fig, ax = plt.subplots(figsize=(8, 5))
                # Plot points, color by SMA ON/OFF
                ax.scatter(trial_disp[trial_sma], trial_temp[trial_sma], color='red', label='SMA ON', alpha=0.7)
                ax.scatter(trial_disp[~trial_sma], trial_temp[~trial_sma], color='blue', label='SMA OFF', alpha=0.7)
                ax.set_xlabel('Displacement [mm]')
                ax.set_ylabel('Temperature [°C]')
                ax.set_title(f'{format_setup_title(prefix)} Run {run_idx}')
                ax.legend()
                fig.tight_layout()
                plt.show()

        # Surface plots for each trial
        print(f"[DEBUG] Creating surface plots for {len(files)} trials...")
        for run_idx in range(1, len(files) + 1):
            trial_mask = trial == run_idx
            if np.any(trial_mask):
                trial_disp = disp[trial_mask]
                trial_temp = temp[trial_mask]
                trial_sma = sma[trial_mask]
                print(f"[DEBUG] Creating surface plot for trial {run_idx} with {len(trial_disp)} points")
                
                # Create time array for this trial (assuming uniform sampling)
                trial_time = np.linspace(0, len(trial_disp)-1, len(trial_disp))
                
                # Create surface plot
                # fig = plt.figure(figsize=(12, 8))
                # ax = fig.add_subplot(111, projection='3d')
                # Create grid for surface interpolation
                xi = np.linspace(trial_disp.min(), trial_disp.max(), 50)
                yi = np.linspace(trial_time.min(), trial_time.max(), 50)
                xi_grid, yi_grid = np.meshgrid(xi, yi)
                
                # Interpolate temperature values for surface
                points = np.column_stack((trial_disp, trial_time))
                zi_grid = griddata(points, trial_temp, (xi_grid, yi_grid), method='linear')
                # Plot surface (DISABLED)
                # surf = ax.plot_surface(xi_grid, yi_grid, zi_grid, 
                #                      cmap='viridis', alpha=0.7, 
                #                      linewidth=0, antialiased=True)
                # Plot original data points on surface (DISABLED)
                # ax.scatter(trial_disp, trial_time, trial_temp, 
                #           c='red' if trial_sma[0] else 'blue', 
                #           s=50, alpha=0.8, edgecolors='black')
                # Color code points by SMA status (DISABLED)
                sma_on_mask = trial_sma
                sma_off_mask = ~trial_sma
                # if np.any(sma_on_mask):
                #     ax.scatter(trial_disp[sma_on_mask], trial_time[sma_on_mask], trial_temp[sma_on_mask],
                #               c='red', s=50, alpha=0.8, edgecolors='black', label='SMA ON')
                # if np.any(sma_off_mask):
                #     ax.scatter(trial_disp[sma_off_mask], trial_time[sma_off_mask], trial_temp[sma_off_mask],
                #               c='blue', s=50, alpha=0.8, edgecolors='black', label='SMA OFF')
                # ax.set_xlabel('Displacement [mm]')
                # ax.set_ylabel('Time [s]')
                # ax.set_zlabel('Temperature [°C]')
                # ax.set_title(f'{format_setup_title(prefix)} Run {run_idx}')
                # Add colorbar (DISABLED)
                # fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
                # ax.legend()
                # plt.tight_layout()
                # plt.show()
    else:
        print(f"[ERROR] No valid data found to plot for {prefix}.")

print("Plotting complete!")
