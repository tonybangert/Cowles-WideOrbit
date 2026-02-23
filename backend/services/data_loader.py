"""
DataLoader — lazy-loading service for WideOrbit sample CSVs.

Reads orders.csv, spots.csv, inventory.csv on first access, then caches
the resulting DataFrames for the lifetime of the process.
"""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import List


DAYPART_NAMES = {
    "EM": "Early Morning",
    "DT": "Daytime",
    "EF": "Early Fringe",
    "EN": "Early News",
    "PA": "Prime Access",
    "PR": "Prime",
    "LN": "Late News",
    "LF": "Late Fringe",
}

DAYPART_ORDER = ["EM", "DT", "EF", "EN", "PA", "PR", "LN", "LF"]


class DataLoader:
    """Lazy-loading cache for WideOrbit sample CSVs."""

    def __init__(self, sample_dir: Path):
        self._dir = sample_dir
        self._orders: pd.DataFrame | None = None
        self._spots: pd.DataFrame | None = None
        self._inventory: pd.DataFrame | None = None

    @property
    def orders(self) -> pd.DataFrame:
        if self._orders is None:
            self._orders = pd.read_csv(
                self._dir / "orders.csv",
                parse_dates=["order_date", "start_date", "end_date"],
            )
        return self._orders

    @property
    def spots(self) -> pd.DataFrame:
        if self._spots is None:
            self._spots = pd.read_csv(
                self._dir / "spots.csv",
                parse_dates=["air_date"],
            )
        return self._spots

    @property
    def inventory(self) -> pd.DataFrame:
        if self._inventory is None:
            self._inventory = pd.read_csv(
                self._dir / "inventory.csv",
                parse_dates=["date"],
            )
        return self._inventory

    def get_stations(self) -> List[str]:
        """Return sorted list of unique station call signs."""
        return sorted(self.spots["station"].unique().tolist())
