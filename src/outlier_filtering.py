"""
outlier_filtering
=================

Functions to remove problematic samples and extreme values from the feature tables.

The original industrial code enforced specific particle count thresholds and
removed rows with extreme Z‑scores.  These utilities implement similar
behaviour in a generic way.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple, List


def filter_by_particle_count(particles: pd.DataFrame, min_count: int, max_count: int) -> Tuple[pd.DataFrame, List[int]]:
    """
    Remove samples whose particle counts fall outside a specified range.

    Parameters
    ----------
    particles : DataFrame
        Particle‑level measurements containing a `SAMPLE_ID` column.
    min_count : int
        Minimum number of particles required for a sample to be kept.
    max_count : int
        Maximum number of particles allowed for a sample to be kept.

    Returns
    -------
    tuple of (DataFrame, list)
        Filtered DataFrame and a list of sample IDs that were removed.
    """
    counts = particles.groupby('SAMPLE_ID').size()
    valid_samples = counts[(counts >= min_count) & (counts <= max_count)].index
    removed_samples = counts[~counts.index.isin(valid_samples)].index.tolist()
    filtered = particles[particles['SAMPLE_ID'].isin(valid_samples)].copy()
    return filtered, removed_samples


def filter_features_by_zscore(features: pd.DataFrame, z_threshold: float) -> pd.DataFrame:
    """
    Remove rows from a feature table based on a Z‑score threshold.  A row is
    discarded if the absolute Z‑score of any feature exceeds `z_threshold`.

    Parameters
    ----------
    features : DataFrame
        Sample‑level feature table including numeric columns and a `SAMPLE_ID`.
    z_threshold : float
        Absolute Z‑score threshold.  Set to None or a non‑positive number to
        disable filtering.

    Returns
    -------
    DataFrame
        Filtered feature table.
    """
    if z_threshold is None or z_threshold <= 0:
        return features
    # Exclude SAMPLE_ID from z‑score computation
    numeric = features.select_dtypes(include=[np.number]).drop(columns=['SAMPLE_ID'], errors='ignore')
    z_scores = np.abs(stats.zscore(numeric, nan_policy='omit'))
    # stats.zscore returns numpy array; when a column has constant value the zscore is NaN
    mask = (z_scores > z_threshold)
    # rows to keep: those with no True values across columns
    keep_rows = ~mask.any(axis=1)
    return features.loc[keep_rows].reset_index(drop=True)
