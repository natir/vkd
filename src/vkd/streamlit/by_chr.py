"""vkd module that generate by_chr streamlit page."""

# std import
from __future__ import annotations

import typing

# 3rd party import
import polars
import streamlit

# project import
import vkd.streamlit

if typing.TYPE_CHECKING:
    # std import
    import pathlib

    # 3rd party import

    # project import


def by_chr(input_directory: pathlib.Path, config_path: pathlib.Path) -> None:
    """Principal function of by_chr page."""
    config = vkd.streamlit.read_config(config_path)

    chr_name_selector = streamlit.sidebar.selectbox(
        "Chromosome",
        vkd.streamlit.chr_list(input_directory),
    )

    lf = polars.scan_parquet(input_directory / f"{chr_name_selector}.parquet")
    lf = lf.select(config["select_column"])

    dataset_name_selector = streamlit.sidebar.selectbox(
        "Dataset name",
        vkd.streamlit.dataset_name(lf),
    )

    subsample_selector = streamlit.sidebar.slider(
        "fraction of dataset",
        min_value=1,
        max_value=100,
        value=1,
    )

    df = vkd.streamlit.by_chr_filtering(
        lf,
        dataset_name_selector,
        chr_name_selector,
        subsample_selector,
    )

    streamlit.title("Coverage by chromosome")
    streamlit.altair_chart(vkd.streamlit.cov_by_chr(df, config))

    streamlit.title("Variant length")
    streamlit.altair_chart(vkd.streamlit.variant_length(df, config))

    streamlit.title("Violin Plot of a specific column")
    column_selector = streamlit.selectbox(
        "Column to show",
        vkd.streamlit.numeric_column(lf),
    )
    streamlit.altair_chart(vkd.streamlit.violin_plot(df, config, column_selector))
