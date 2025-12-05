"""vkd package.

Variant Knowledge Dashboard
"""

# std import
from __future__ import annotations

# 3rd party import
# project import
from vkd import reader, writer
from vkd import streamlit
from vkd._internal.cli import main

__all__: list[str] = ["main", "reader", "writer", "streamlit"]
