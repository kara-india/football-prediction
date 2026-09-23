"""
Odds Engine Package
Mathematical devigging, Shin's method, and odds snapshot logging.
"""
from .devig import DeVIgEngine
from .snapshot_writer import OddsSnapshotWriter

__all__ = ["DeVIgEngine", "OddsSnapshotWriter"]
