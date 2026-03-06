"""
visualization
=============

Matplotlib‑based helper functions for common plots.  These are intentionally
simple so they can be used in scripts or notebooks without interactive
dependencies.  Plotly was used in the original project but here we
standardise on matplotlib to avoid heavy dependencies in non‑browser
environments.
"""

from __future__ import annotations

import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict


def plot_particle_count_distribution(particles: pd.DataFrame, output_dir: str) -> None:
    """
    Create a histogram and line plot of the number of particles per sample.  Two
    PNG files are saved into `output_dir`.

    Parameters
    ----------
    particles : DataFrame
        Particle‑level measurements containing a `SAMPLE_ID` column.
    output_dir : str
        Directory into which the plots will be saved.
    """
    counts = particles.groupby('SAMPLE_ID').size()
    os.makedirs(output_dir, exist_ok=True)
    # Histogram
    plt.figure()
    counts.plot.hist(bins=20)
    plt.title('Distribution of Particle Counts per Sample')
    plt.xlabel('Particle Count')
    plt.ylabel('Frequency')
    hist_path = os.path.join(output_dir, 'particle_count_histogram.png')
    plt.savefig(hist_path)
    plt.close()
    # Line plot
    plt.figure()
    plt.plot(counts.index, counts.values)
    plt.title('Particle Counts per Sample')
    plt.xlabel('Sample ID')
    plt.ylabel('Particle Count')
    line_path = os.path.join(output_dir, 'particle_count_lineplot.png')
    plt.savefig(line_path)
    plt.close()


def plot_elongation_distribution(features: pd.DataFrame, output_dir: str) -> None:
    """
    Plot the distribution and empirical CDF of sample‑level elongation values.

    Parameters
    ----------
    features : DataFrame
        Feature table containing an `ELONGATION_mean` column produced by
        `aggregate_sample_features`.
    output_dir : str
        Directory into which the plot will be saved.
    """
    if 'ELONGATION_mean' not in features.columns:
        raise ValueError('ELONGATION_mean column not found; ensure you computed elongation before aggregating.')
    values = features['ELONGATION_mean'].dropna().values
    os.makedirs(output_dir, exist_ok=True)
    plt.figure()
    # Histogram
    plt.hist(values, bins=20, density=True)
    plt.title('Distribution of Elongation (Sample‑level means)')
    plt.xlabel('Elongation')
    plt.ylabel('Density')
    # CDF
    sorted_vals = np.sort(values)
    cdf = np.arange(1, len(sorted_vals) + 1) / len(sorted_vals)
    plt.twinx()
    plt.plot(sorted_vals, cdf)
    plt.ylabel('CDF')
    out_path = os.path.join(output_dir, 'elongation_distribution_cdf.png')
    plt.savefig(out_path)
    plt.close()


def plot_correlation_heatmap(corr_df: pd.DataFrame, output_path: str) -> None:
    """
    Plot a heatmap of correlation coefficients.  The input should be a wide
    DataFrame where rows are features and columns are target variables.

    Parameters
    ----------
    corr_df : DataFrame
        DataFrame of correlation coefficients; features are the index.
    output_path : str
        Destination path for the PNG file.
    """
    import seaborn as sns
    plt.figure(figsize=(max(6, corr_df.shape[1] * 1.2), max(6, corr_df.shape[0] * 0.3)))
    sns.heatmap(corr_df, annot=True, fmt='.2f', cmap='coolwarm', cbar=True)
    plt.title('Feature‑Target Correlation Heatmap')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
