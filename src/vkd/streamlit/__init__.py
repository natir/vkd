"""vkd module that generate streamlit interface."""

# std import
from __future__ import annotations

import os
import pathlib
import typing

# 3rd party import
import altair
import polars
import streamlit
import tomllib

# project import

if typing.TYPE_CHECKING:
    # std import
    import pathlib

    # 3rd party import

    # project import


def main(enable_pages: list[str]) -> None:
    """Streamlit main page."""
    altair.data_transformers.disable_max_rows()

    pages = streamlit.navigation([streamlit.Page(f"{p}.py") for p in enable_pages])

    pages.run()


def read_config(config: pathlib.Path) -> dict[str, typing.Any]:
    """Read configuration file."""
    with open(config, "rb") as fh:
        return tomllib.load(fh)


def axis_title(config: dict[str, typing.Any], col_name: str) -> str:
    """Return axis with alias if set."""
    return config["alias"].get(col_name, col_name)


def dataset_name(_lf: polars.LazyFrame) -> list[str]:
    """Extract list of dataset in LazyFrame."""
    return _lf.select("dataset").unique().sort("dataset").collect().get_column("dataset").to_list()


@streamlit.cache_data
def chr_list(input_directory: pathlib.Path) -> list[str]:
    """Extract chromosome from input directory."""
    result = []

    with os.scandir(input_directory) as dir_scan:
        for entry in dir_scan:
            if entry.is_file() and entry.name.endswith(".parquet"):
                result.append(entry.name.split(".")[0])

    return result


@streamlit.cache_data
def numeric_column(_lf: polars.LazyFrame) -> list[str]:
    """Generate plotable numeric value."""
    return [
        name
        for name, col_type in dict(_lf.collect_schema()).items()
        if col_type
        in [
            polars.Float32,
            polars.Float64,
            polars.Int8,
            polars.Int16,
            polars.Int32,
            polars.Int64,
            polars.Int128,
            polars.UInt8,
            polars.UInt16,
            polars.UInt32,
            polars.UInt64,
        ]
    ]


@streamlit.cache_data
def by_chr_filtering(
    _lf: polars.LazyFrame,
    dataset: str,
    chr_name: str,
    fraction: int,
) -> polars.DataFrame:
    """Filter data in LazyFrame and collect it in dataframe."""
    return (
        _lf.filter(polars.col("chr") == chr_name)
        .filter(polars.col("dataset") == dataset)
        .collect()
        .sample(fraction=fraction / 100)
    )


@streamlit.cache_data
def cov_by_chr(df: polars.DataFrame, config: dict[str, typing.Any]) -> altair.Chart:
    """Generate plot coverage of each variant."""
    df = df.select("position", "format_dp", "format_bd")
    return (
        altair.Chart(df)
        .mark_point(shape="circle", filled=True, size=10)
        .encode(
            x=altair.X("position").title(axis_title(config, "position")),
            y=altair.Y("format_dp").title(axis_title(config, "format_dp")),
            color=altair.Color("format_bd").title(axis_title(config, "format_bd")),
        )
    )


@streamlit.cache_data
def violin_plot(
    df: polars.DataFrame,
    config: dict[str, typing.Any],
    column: str,
) -> altair.Chart:
    """Generate a violin plot of selected column."""
    df = df.select(column, "format_bd")

    return (
        altair.Chart(df)
        .transform_density(
            column,
            as_=[column, "density"],
            groupby=["format_bd"],
        )
        .mark_area(orient="horizontal")
        .encode(
            altair.X("density:Q")
            .stack("center")
            .impute(None)
            .title(None)
            .axis(labels=False, values=[0], grid=False, ticks=True)
            .title(axis_title(config, column)),
            altair.Y(column).title(axis_title(config, column)),
            altair.Color("format_bd").title(axis_title(config, "format_bd")),
            altair.Column("format_bd")
            .spacing(0)
            .header(titleOrient="bottom", labelOrient="bottom", labelPadding=0)
            .title(axis_title(config, "format_bd")),
        )
        .configure_view(
            stroke=None,
        )
    )


@streamlit.cache_data
def variant_length(df: polars.DataFrame, config: dict[str, typing.Any]) -> altair.Chart:
    """Generate a plot of variant length."""
    df = (
        df.select("ref", "alt", "format_bd")
        .with_columns(
            variant_length=polars.col("ref").str.len_chars().cast(polars.Int32)
            - polars.col("alt").str.len_chars().cast(polars.Int32),
        )
        .group_by("variant_length", "format_bd")
        .len()
    )

    return (
        altair.Chart(df)
        .mark_line()
        .encode(
            altair.X("variant_length"),
            altair.Y("len").scale(type="log").title(axis_title(config, "len")),
            altair.Color("format_bd").title(axis_title(config, "format_bd")),
        )
    )
