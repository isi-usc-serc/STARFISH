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
import re

# Path to data directory
DATA_DIR = r"C:\Users\Owner\Desktop\SERC\STARFISH_Project\Software\STARFISH\Thermo_Position_Data"

# Find all run CSV files
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "*V_*A_*G_run_*.csv")))

all_displacement = []
all_temp = []
all_trial = []
all_sma = []
all_titles = []

for run_idx, csv_path in enumerate(csv_files, 1):
    df = pd.read_csv(csv_path)
    # Ensure columns exist
    if not all(col in df.columns for col in ["x", "y", "tc1", "sma_active"]):
        print(f"[WARN] Missing columns in {csv_path}, skipping.")
        continue
    if df.empty:
        print(f"[WARN] {csv_path} is empty, skipping.")
        continue
    # Parse filename for parameters
    fname = os.path.basename(csv_path)
    match = re.match(r"(\d+)p(\d+)V_(\d+)p(\d+)A_(\d+)G_run_\d+", fname)
    if match:
        volts = f"{match.group(1)}.{match.group(2)}"
        amps = f"{match.group(3)}.{match.group(4)}"
        grams = match.group(5)
        title = f"SMA Characterization for {volts}V, {amps}A, {grams}G"
    else:
        title = "SMA Characterization"
    all_titles.append(title)
    # Calculate displacement from initial x/y
    first_row = df.iloc[0]
    x0, y0 = first_row["x"], first_row["y"]
    displacement = np.sqrt((df["x"] - x0) ** 2 + (df["y"] - y0) ** 2)
    temp = df["tc1"]
    trial = np.full_like(displacement, run_idx, dtype=float)
    sma = df["sma_active"].astype(bool)
    all_displacement.append(displacement)
    all_temp.append(temp)
    all_trial.append(trial)
    all_sma.append(sma)

# Concatenate all runs
if all_displacement:
    disp = np.concatenate(all_displacement)
    temp = np.concatenate(all_temp)
    trial = np.concatenate(all_trial)
    sma = np.concatenate(all_sma)

    # Set color: red if SMA active, blue if not
    colors = np.where(sma, 'red', 'blue')

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    for c in [True, False]:
        mask = sma == c
        ax.scatter(disp[mask], temp[mask], trial[mask],
                   c='red' if c else 'blue', label='SMA ON' if c else 'SMA OFF', marker='o', alpha=0.7)
    ax.set_xlabel('Displacement (pixels)')
    ax.set_ylabel('Temperature (°C)')
    ax.set_zlabel('Trial Number')
    plt.title(all_titles[0] if all_titles else 'SMA Characterization')
    ax.legend()
    plt.tight_layout()
    plt.show()
else:
    print("[ERROR] No valid data found to plot.")