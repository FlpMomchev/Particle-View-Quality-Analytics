#!/usr/bin/env python
"""
run_pipeline
============

Command‑line entry point for the industrial particle analysis pipeline.

This script reads configuration from a YAML file, loads raw CSVs, applies
filtering and feature engineering, and computes simple correlations to
quality metrics.  Results are saved into the `output_dir` specified in
the configuration.
"""

from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

from utils import load_config, ensure_output_dir
import feature_engineering as fe
import outlier_filtering as of
import correlation_analysis as ca
import visualization as vz


def main(config_path: str) -> None:
    # Load configuration
    config = load_config(config_path)
    output_dir = config.get('output_dir', 'outputs')
    ensure_output_dir(output_dir)

    # Load particle data
    particle_path = config['particle_data']
    particles = fe.load_particle_data(particle_path)

    # Filter samples by particle count
    min_count = config.get('min_particles_per_sample', 1)
    max_count = config.get('max_particles_per_sample', int(1e9))
    particles_filtered, removed_samples = of.filter_by_particle_count(particles, min_count, max_count)
    if removed_samples:
        print(f"Removed {len(removed_samples)} samples outside count range: {removed_samples}")

    # Plot particle count distribution
    vz.plot_particle_count_distribution(particles_filtered, output_dir)

    # Aggregate particle features to sample level
    feature_table = fe.aggregate_sample_features(particles_filtered)

    # Remove constant features and highly correlated features
    feature_table = fe.remove_constant_features(feature_table, min_unique=3)
    feature_table = fe.remove_highly_correlated_features(feature_table, threshold=0.95)

    # Save raw feature table
    features_csv = os.path.join(output_dir, 'features_raw.csv')
    feature_table.to_csv(features_csv, index=False)

    # Filter outlier rows by z‑score if specified
    zthr = config.get('zscore_threshold', None)
    feature_table_filtered = of.filter_features_by_zscore(feature_table, zthr)
    filtered_csv = os.path.join(output_dir, 'features_filtered.csv')
    feature_table_filtered.to_csv(filtered_csv, index=False)

    # Plot elongation distribution (using the mean elongation column)
    try:
        vz.plot_elongation_distribution(feature_table_filtered, output_dir)
    except Exception as e:
        print(f"Unable to plot elongation distribution: {e}")

    # Perform correlation analysis if quality data and targets are provided
    quality_path = config.get('quality_data')
    targets = config.get('correlation_targets', [])
    if quality_path and targets:
        quality_df = pd.read_csv(quality_path)
        # Compute correlations across all samples
        corr_results = ca.compute_correlations(feature_table_filtered, quality_df, targets)
        # Save each target's correlation table as CSV
        for target, df in corr_results.items():
            corr_csv = os.path.join(output_dir, f'correlations_{target}.csv')
            df.to_csv(corr_csv, index=False)
        # Optionally produce a heatmap by pivoting the results
        heatmap_df = pd.DataFrame({t: corr_results[t].set_index('Feature')['Correlation'] for t in corr_results}).fillna(0)
        heatmap_path = os.path.join(output_dir, 'correlation_heatmap.png')
        vz.plot_correlation_heatmap(heatmap_df, heatmap_path)
    else:
        print("Quality data or correlation targets not provided; skipping correlation analysis.")

    print(f"Pipeline finished.  Outputs written to {output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the industrial particle analysis pipeline.')
    parser.add_argument('--config', type=str, required=True, help='Path to YAML configuration file.')
    args = parser.parse_args()
    try:
        main(args.config)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)