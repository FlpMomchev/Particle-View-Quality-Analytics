"""
material_alignment
==================

Functions to align particle samples with process/material data using timestamps.

The original project needed to match particle view samples to material numbers
from a cooling line database.  This module implements a few generic routines
for that purpose.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Tuple


def get_material_numbers_in_sample_range(particle_view: pd.DataFrame, process_df: pd.DataFrame,
                                         start_sample_id: int, end_sample_id: int) -> Tuple[List, pd.Timestamp, pd.Timestamp]:
    """
    Determine which material numbers were produced during the time span covered
    by a range of sample IDs.

    Parameters
    ----------
    particle_view : DataFrame
        Particle‑level measurements with `SAMPLE_ID` and `DATATIMESTAMP`.
    process_df : DataFrame
        Process data with `DATATIMESTAMP` and `MATERIALNO` columns.
    start_sample_id : int
        First sample ID in the range.
    end_sample_id : int
        Last sample ID in the range.

    Returns
    -------
    (list, Timestamp, Timestamp)
        Unique material numbers present in the time window, the start timestamp of
        the first sample, and the end timestamp of the last sample.
    """
    # find timestamps of start and end sample IDs
    start_time = particle_view.loc[particle_view['SAMPLE_ID'] == start_sample_id, 'DATATIMESTAMP'].iloc[0]
    end_time = particle_view.loc[particle_view['SAMPLE_ID'] == end_sample_id, 'DATATIMESTAMP'].iloc[0]
    # filter process data for this window
    mask = (process_df['DATATIMESTAMP'] >= start_time) & (process_df['DATATIMESTAMP'] <= end_time)
    materials = process_df.loc[mask, 'MATERIALNO'].unique().tolist()
    return materials, start_time, end_time


def find_material_periods(process_df: pd.DataFrame, material_numbers: List) -> Dict:
    """
    Find continuous periods when each material number appears in the process data.

    Parameters
    ----------
    process_df : DataFrame
        Process data with `DATATIMESTAMP` and `MATERIALNO`.
    material_numbers : list
        Material numbers to consider.

    Returns
    -------
    dict
        Mapping from material number to a list of (start_time, end_time)
        tuples for each contiguous period when the material was present.
    """
    periods: Dict = {}
    for material in material_numbers:
        periods[material] = []
        start = None
        end = None
        running = False
        for _, row in process_df.iterrows():
            if row['MATERIALNO'] == material:
                if not running:
                    start = row['DATATIMESTAMP']
                    running = True
                end = row['DATATIMESTAMP']
            else:
                if running:
                    periods[material].append((start, end))
                    running = False
        # catch a run that continues to the end
        if running:
            periods[material].append((start, end))
    return periods


def find_sample_ids_in_ranges(particle_view: pd.DataFrame,
                              start_tuple: Tuple[pd.Timestamp, pd.Timestamp],
                              end_tuple: Tuple[pd.Timestamp, pd.Timestamp]) -> Dict[str, Tuple[List[int], int]]:
    """
    Find sample IDs that fall between specified timestamp tuples.  This helper
    identifies samples that lie between the start of the particle range and
    the start of the first material period, and between the end of the last
    material period and the end of the particle range.

    Parameters
    ----------
    particle_view : DataFrame
        Particle data with `SAMPLE_ID` and `DATATIMESTAMP`.
    start_tuple : (Timestamp, Timestamp)
        (timestamp of the first sample, timestamp of the first relevant material start)
    end_tuple : (Timestamp, Timestamp)
        (timestamp of the last sample, timestamp of the last relevant material end)

    Returns
    -------
    dict
        Keys are 'before_start' and 'after_end'; each value is a tuple
        (list of sample IDs, count).
    """
    start_sample_time, material_start_time = start_tuple
    end_sample_time, material_end_time = end_tuple
    # samples between the material start and the first sample
    before = particle_view[(particle_view['DATATIMESTAMP'] >= material_start_time) &
                           (particle_view['DATATIMESTAMP'] <= start_sample_time)]['SAMPLE_ID'].unique().tolist()
    after = particle_view[(particle_view['DATATIMESTAMP'] >= end_sample_time) &
                          (particle_view['DATATIMESTAMP'] <= material_end_time)]['SAMPLE_ID'].unique().tolist()
    return {
        'before_start': (before, len(before)),
        'after_end': (after, len(after))
    }
