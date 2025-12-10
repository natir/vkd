"""vkd module that generate generic streamlit page."""

# std import
from __future__ import annotations

import os
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


def generic(input_directory: pathlib.Path, config_path: pathlib.Path) -> None:
    """Principal function of generic page."""
    config = vkd.streamlit.read_config(config_path)

    lfs = []
    with os.scandir(input_directory) as dir_scan:
        for entry in dir_scan:
            if entry.is_file() and entry.name.endswith(".parquet") and entry.stat().st_size > 0:
                lfs.append(
                    polars.scan_parquet(entry.path).select(config["select_column"]),
                )

    lf = polars.concat(lfs)

    dataset_name_selector = streamlit.sidebar.selectbox(
        "dataset",
        vkd.streamlit.dataset_name(lf),
    )

    streamlit.title("Repartition of variant by chromosome and type.")
    count_by_chr = (
        lf.filter(polars.col("dataset") == dataset_name_selector).group_by("chr", "format_bd").len().collect()
    )

    streamlit.altair_chart(
        altair.Chart(count_by_chr)
        .mark_line()
        .encode(
            altair.X("chr").sort(vkd.streamlit.chr_list(input_directory)).title(vkd.streamlit.axis_title(config, "chr")),
            altair.Y("len").scale(type="log").title(vkd.streamlit.axis_title(config, "len")),
            altair.Color("format_bd").title(
                vkd.streamlit.axis_title(config, "format_bd"),
            ),
        ),
    )
