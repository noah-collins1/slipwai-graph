"""The four files the factory seeds and a project then owns: a refresh leaves them where they are.

`.specify/cruise.json`, `product-owner.md`, `models.json` and `drive.json` are written once, with defaults, and
changed by the project from then on — a run's settings, the owner's brief, which model runs each stage. A refresh
that wrote them back to the factory's default reset the project's work, so it writes one only where it is absent.
"""
from __future__ import annotations

from pathlib import Path

from ..layout import Layout
from .cruise_record import CONFIG as CRUISE
from .decisions import PAGE as OWNER_BRIEF
from .drive_settings import CONFIG as DRIVE

MODELS = ".specify/models.json"
SEEDED = (CRUISE, OWNER_BRIEF, MODELS, DRIVE)


def kept(root: Path, layout: Layout) -> set[str]:
    """Those of the four that are on disk, as the layout places them: the ones a refresh does not touch."""
    return {path for path in map(layout.place, SEEDED) if (root / path).is_file()}
