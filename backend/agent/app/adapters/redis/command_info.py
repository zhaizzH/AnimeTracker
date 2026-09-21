"""``COMMAND INFO`` response parsing shared by every Vector Set capability check.

This module is the single definition of ``command_info_present``.  It must stay
free of internal imports: ``vector_set`` already imports ``subject_index``, so a
second copy (or an import in the other direction) would either duplicate the
decision logic or create an import cycle.
"""

from __future__ import annotations

from typing import Any, Mapping


def command_info_present(info: Any) -> bool:
    """Redis returns ``[None]`` for an unknown COMMAND INFO entry."""
    if not info:
        return False
    if isinstance(info, Mapping):
        return any(item is not None for item in info.values())
    if isinstance(info, (list, tuple)):
        return any(item is not None for item in info)
    return True
