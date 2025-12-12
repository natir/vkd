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
    print("by_chr")
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

    df = filter_and_collect(
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

    streamlit.title("Variant length")
    streamlit.altair_chart(
        vkd.streamlit.line_chart(
            variant_length_histo(df, [config["alias"]["format_bd"]]), "var_len", "len", config["alias"]["format_bd"]
        ),
    )

    streamlit.title("Violin Plot of a specific column")
    column_selector = streamlit.selectbox(
        "Column to show",
        vkd.streamlit.numeric_column(lf),
    )
    streamlit.altair_chart(vkd.streamlit.violin_plot(df, config, column_selector))


@streamlit.cache_data
def filter_and_collect(_lf: polars.LazyFrame, cols_values: list[(str, typing.Any)], fraction: int) -> polars.DataFrame:
    """Filter on column and collect lazyframe."""
    return vkd.streamlit.collect_and_sample(
        _lf.filter([polars.col(col) == value for col, value in cols_values]),
        fraction,
    )


@streamlit.cache_data
def variant_length_histo(df: polars.DataFrame, keep_col: list[str]) -> polars.DataFrame:
    """Compute and collect variant length."""
    return (
        df.with_columns(
            var_len=polars.col("ref").str.len_chars().cast(polars.Int64)
            - polars.col("alt").str.len_chars().cast(polars.Int64),
        )
        .group_by("chr", "position", "ref", "alt", "var_len", *keep_col)
        .len()
        .select(*keep_col, "var_len", "len")
    )
