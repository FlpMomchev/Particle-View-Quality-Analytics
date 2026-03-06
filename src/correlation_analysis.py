"""
correlation_analysis
====================

Functions for computing correlations between sample‑level features and quality metrics.

The production version of this code generated Excel files and per‑material
directories.  This simplified version returns pandas DataFrames so that the
results can be inspected or exported as needed.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Dict, Optional


def compute_correlations(features_df: pd.DataFrame, quality_df: pd.DataFrame,
                         target_columns: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Compute Pearson correlations between each feature and one or more target
    variables.

    Parameters
    ----------
    features_df : DataFrame
        Feature table with `SAMPLE_ID` and numeric feature columns.
    quality_df : DataFrame
        Quality metrics table with `SAMPLE_ID` and the specified targets.
    target_columns : list of str
        Column names in `quality_df` to correlate against.

    Returns
    -------
    dict
        Mapping from target column name to a DataFrame with two columns:
        `Feature` and `Correlation`.
    """
    # join on SAMPLE_ID
    features = features_df.set_index('SAMPLE_ID')
    quality = quality_df.set_index('SAMPLE_ID')[target_columns]
    joined = features.join(quality, how='inner')
    result: Dict[str, pd.DataFrame] = {}
    for target in target_columns:
        corr_series = joined.corr()[target].drop(target)
        result[target] = pd.DataFrame({
            'Feature': corr_series.index,
            'Correlation': corr_series.values
        }).sort_values(by='Correlation', ascending=False).reset_index(drop=True)
    return result


def compute_correlations_by_material(features_df: pd.DataFrame, quality_df: pd.DataFrame,
                                     material_series: pd.Series, target_columns: List[str]) -> Dict[str, Dict[str, pd.DataFrame]]:
    """
    Compute correlations separately for each material number.

    Parameters
    ----------
    features_df : DataFrame
        Feature table with `SAMPLE_ID`.
    quality_df : DataFrame
        Quality metrics table with `SAMPLE_ID`.
    material_series : Series
        Series indexed by `SAMPLE_ID` mapping each sample to its material code.
    target_columns : list of str
        Target variables to correlate.

    Returns
    -------
    dict
        Nested mapping: material_code -> { target -> correlation DataFrame }.
    """
    result: Dict[str, Dict[str, pd.DataFrame]] = {}
    # ensure material_series has SAMPLE_ID as index
    material_series = material_series.drop_duplicates().set_index('SAMPLE_ID')['MATERIALNO'] if isinstance(material_series, pd.DataFrame) else material_series
    for material in material_series.unique():
        sample_ids = material_series[material_series == material].index
        feat_subset = features_df[features_df['SAMPLE_ID'].isin(sample_ids)].copy()
        qual_subset = quality_df[quality_df['SAMPLE_ID'].isin(sample_ids)].copy()
        # skip if no samples
        if len(feat_subset) < 2:
            continue
        result[material] = compute_correlations(feat_subset, qual_subset, target_columns)
    return result
