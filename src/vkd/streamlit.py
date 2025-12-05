"""vkd module that generate streamlit interface."""

# std import
from __future__ import annotations

import pathlib

# 3rd party import
import polars
import streamlit

# project import


def main(input_path: pathlib.path) -> None:
    """TODO."""
    lf = polars.scan_parquet(input_path)
    lf = lf.filter(polars.col("chr") == "chr22")
    lf = lf.select("position", "format_dp", "format_bd")

    streamlit.scatter_chart(lf.collect(), x="position", y="format_dp", color="format_bd", size=10)
