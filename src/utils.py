"""
utils
=====

Miscellaneous helper functions for file I/O and configuration.
"""

from __future__ import annotations

import os
import yaml

from typing import Any, Dict


def load_config(path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    path : str
        Path to the YAML file.

    Returns
    -------
    dict
        Parsed configuration.
    """
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def ensure_output_dir(path: str) -> None:
    """Create the output directory if it does not already exist."""
    os.makedirs(path, exist_ok=True)
