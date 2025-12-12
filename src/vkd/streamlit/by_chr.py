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


"""Maximal variant length."""
MAX_VARIANT_LENGTH = 50


def by_chr(input_directory: pathlib.Path, config_path: pathlib.Path) -> None:
    """Principal function of by_chr page."""
    config = vkd.streamlit.read_config(config_path)

    chr_name_selector = streamlit.sidebar.selectbox(
        "Chromosome",
        vkd.streamlit.scan_chr_list(input_directory),
    )

    lf = vkd.streamlit.read_parquet(input_directory, chr_name_selector, config)

    dataset_name_selector = streamlit.sidebar.selectbox(
        "Dataset name",
        vkd.streamlit.extract_dataset_name(lf, config),
    )

    subsample_selector = streamlit.sidebar.slider(
        "fraction of dataset",
        min_value=1,
        max_value=100,
        value=1,
    )

    df = vkd.streamlit.filter_and_collect(
        lf,
        [
            (config["alias"]["dataset"], dataset_name_selector),
            (config["alias"]["chr"], chr_name_selector),
        ],
        subsample_selector,
    )

    streamlit.title("Coverage by chromosome")
    streamlit.altair_chart(
        vkd.streamlit.scatter_chart(
            df,
            config["alias"]["position"],
            config["alias"]["format_dp"],
            config["alias"]["format_bd"],
        ),
    )

    streamlit.title("Variant length:")
    y_scale = streamlit.selectbox(
        "Y scale",
        config["altair_scale"],
    )
    streamlit.altair_chart(
        vkd.streamlit.line_chart(
            variant_length_histo(df, [config["alias"]["format_bd"]]),
            "var_len",
            "len",
            config["alias"]["format_bd"],
            y_scale=y_scale,
        ),
    )

    streamlit.title("Violin Plot of a specific column:")
    column_selector = streamlit.selectbox(
        "Column to show",
        vkd.streamlit.numeric_column(lf),
    )
    plot = vkd.streamlit.violin_chart(
        vkd.streamlit.one_column(
            df,
            column_selector,
            [config["alias"]["format_bd"]],
        ),
        column_selector,
        config["alias"]["format_bd"],
    )
    streamlit.altair_chart(
        plot,
    )


@streamlit.cache_data
def variant_length_histo(df: polars.DataFrame, keep_col: list[str]) -> polars.DataFrame:
    """Compute and collect variant length."""
    return (
        df.with_columns(
            var_len=polars.col("ref").str.len_chars().cast(polars.Int64)
            - polars.col("alt").str.len_chars().cast(polars.Int64),
        )
        .filter(polars.col("var_len") < MAX_VARIANT_LENGTH)
        .group_by("var_len", *keep_col)
        .len()
        .select(*keep_col, "var_len", "len")
    )
