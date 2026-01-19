import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO") -> None:
    """
    Simple, structured-ish logging.
    """
    numeric_level: Optional[int] = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    root = logging.getLogger()
    root.setLevel(numeric_level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    # Clear existing handlers to avoid duplicate logs in reloads
    root.handlers.clear()
    root.addHandler(handler)
