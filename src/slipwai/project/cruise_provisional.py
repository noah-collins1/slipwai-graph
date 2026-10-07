"""What `/cruise` says about provisional decisions (S27), kept out of `cruise.py` so that file stays within its cap.

One constant per sentence or list, imported by the writers of the settings table and the command; the toolkit's
`scripts/agents/cruise.py` cannot import from here, so a test holds its copy to these.
"""
from __future__ import annotations

DECIDE_VALUES: tuple[str, ...] = (
    "recommended-first", "skipper-always", "provisional-shadow", "provisional-advisory", "provisional",
)
DECIDE_CONTROLS = (
    "who answers a product question: the host where the stage recommends an answer or a standing decision covers "
    "it and `drive-skipper` otherwise, or `drive-skipper` for every question. Change it to `provisional-shadow` "
    "when always-ask questions are stalling slices and you want to see which ones would have been taken "
    "provisionally before letting any be; move on to `provisional-advisory`, then `provisional`, once the shadow "
    "lines read right."
)
