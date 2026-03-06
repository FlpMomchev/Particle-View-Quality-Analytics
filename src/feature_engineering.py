"""
feature_engineering
===================

Utilities for transforming raw particle measurements into a cleaned feature table.

The functions in this module operate on pandas DataFrames.  They were extracted
from a much larger internal script and simplified for clarity.  Feel free to
extend them for your own use cases.
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import List, Tuple


def load_particle_data(path: str) -> pd.DataFrame:
    """
    Load particle‑level measurements from a CSV file.  The expected schema is
    described in `data/README.md`.

    Parameters
    ----------
    path : str
        Path to the particle CSV.

    Returns
    -------
    DataFrame
        Raw particle measurements.
    """
    df = pd.read_csv(path)
    if 'DATATIMESTAMP' in df.columns:
        # parse timestamps if present
        df['DATATIMESTAMP'] = pd.to_datetime(df['DATATIMESTAMP'])
    return df


def compute_elongation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the elongation of each particle based on its length, width and
    thickness.  Elongation is defined as (max(L,W,T) – min(L,W,T)) / mean(L,W,T).

    The result is added as a new `ELONGATION` column and returned.

    Parameters
    ----------
    df : DataFrame
        Particle‑level measurements containing `LENGTH`, `WIDTH` and
        `THICKNESS_AVG` columns.

    Returns
    -------
    DataFrame
        Copy of the input with an additional `ELONGATION` column.
    """
    df = df.copy()
    dims = df[['LENGTH', 'WIDTH', 'THICKNESS_AVG']]
    df['ELONGATION'] = (dims.max(axis=1) - dims.min(axis=1)) / dims.mean(axis=1)
    return df


def aggregate_sample_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate particle‑level measurements into sample‑level summary statistics.

    For each `SAMPLE_ID` the following statistics are computed for the numeric
    columns (including the elongation calculated via `compute_elongation`):

    * mean
    * standard deviation
    * minimum
    * 25th percentile
    * median
    * 75th percentile
    * maximum

    The resulting DataFrame has one row per sample and columns formatted as
    `<feature>_<stat>`.  Non‑numeric columns are ignored.

    Parameters
    ----------
    df : DataFrame
        Particle‑level measurements including a `SAMPLE_ID` column.

    Returns
    -------
    DataFrame
        Sample‑level feature table.
    """
    if 'ELONGATION' not in df.columns:
        df = compute_elongation(df)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # drop PARTICLE_ID because it is just an identifier
    numeric_cols = [c for c in numeric_cols if c not in ('PARTICLE_ID',)]

    agg_funcs = {
        'mean': np.mean,
        'std': np.std,
        'min': np.min,
        '25pct': lambda x: np.percentile(x, 25),
        'median': np.median,
        '75pct': lambda x: np.percentile(x, 75),
        'max': np.max,
    }

    grouped = df.groupby('SAMPLE_ID')[numeric_cols]
    # build a dict of {stat_name: agg_func} for pandas aggregate
    agg_dict = {stat: func for stat, func in agg_funcs.items()}
    agg_df = grouped.agg(agg_dict)

    # Flatten the multiindex columns (statistic, original column)
    agg_df.columns = [f"{col}_{stat}" for stat in agg_funcs.keys() for col in numeric_cols]
    agg_df.reset_index(inplace=True)
    return agg_df


def remove_constant_features(df: pd.DataFrame, min_unique: int = 3) -> pd.DataFrame:
    """
    Remove features (columns) with fewer than `min_unique` unique values.  Such
    features carry little information and can cause numerical issues in later
    analysis.

    Parameters
    ----------
    df : DataFrame
        Input feature table.
    min_unique : int, optional
        Minimum number of unique values required to keep a column.  Defaults
        to 3.

    Returns
    -------
    DataFrame
        Copy of the input with constant columns dropped.
    """
    to_drop = [c for c in df.columns if df[c].nunique() < min_unique and c != 'SAMPLE_ID']
    return df.drop(columns=to_drop)


def remove_highly_correlated_features(df: pd.DataFrame, threshold: float = 0.95) -> pd.DataFrame:
    """
    Remove features that are highly correlated with each other.  This simple
    implementation computes the Pearson correlation matrix and drops one
    variable from each pair of columns whose absolute correlation exceeds the
    given threshold.

    Parameters
    ----------
    df : DataFrame
        Input feature table.  Assumes numeric columns only, except for
        `SAMPLE_ID`.
    threshold : float, optional
        Correlation threshold above which one of the two correlated
        features will be removed.  Defaults to 0.95.

    Returns
    -------
    DataFrame
        Copy of the input with correlated columns dropped.
    """
    df_num = df.select_dtypes(include=[np.number]).drop(columns=['SAMPLE_ID'], errors='ignore')
    corr_matrix = df_num.corr().abs()
    # track columns to drop
    to_drop = set()
    for i, col in enumerate(corr_matrix.columns):
        if col in to_drop:
            continue
        for j in range(i + 1, len(corr_matrix.columns)):
            other = corr_matrix.columns[j]
            if corr_matrix.iloc[i, j] > threshold:
                to_drop.add(other)
    return df.drop(columns=list(to_drop))
