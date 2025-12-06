"""vkd module that generate generic streamlit page."""

# std import
from __future__ import annotations

import typing

# 3rd party import
import altair
import polars
import streamlit

# project import
import vkd.streamlit

if typing.TYPE_CHECKING:
    # std import
    import pathlib

    # 3rd party import

    # project import


def generic(input_path: pathlib.Path) -> None:
    """Principal function of generic page."""
    lf = polars.scan_parquet(input_path)

    dataset_name_selector = streamlit.sidebar.selectbox("dataset", vkd.streamlit.dataset_name(lf))

    streamlit.title("TP and FP by chromosome")
    count_by_chr = (
        lf.filter(polars.col("dataset") == dataset_name_selector).group_by("chr", "format_bd").len().collect()
    )

    streamlit.altair_chart(
        altair.Chart(count_by_chr)
        .mark_line()
        .encode(
            altair.X("chr").sort(vkd.streamlit.chr_list(lf)),
            altair.Y("len").scale(type="log"),
            altair.Color("format_bd"),
        ),
    )
