"""vkd module that generate streamlit interface."""

# std import
from __future__ import annotations

import os
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


def read_config(config_path: pathlib.Path) -> dict[str, typing.Any]:
    """Read configuration file."""
    with open(config_path, "rb") as fh:
        config = tomllib.load(fh)

    config["select_column"].extend(
        [
            col_name
            for col_name in ["chr", "position", "ref", "alt", "dataset"]
            if col_name not in config["select_column"]
        ],
    )

    config["alias"].update(
        {key: key for key in config["select_column"] if key not in config["alias"]},
    )

    return config


def read_parquet(input_directory: pathlib.Path, chr_name: str, config: dict[str, typing.Any]) -> polars.LazyFrame:
    """Read a parquet file in polars.LazyFrame and apply change."""
    lf = polars.scan_parquet(input_directory / f"{chr_name}.parquet")

    lf = lf.select(config["select_column"])
    lf = lf.rename({key: name for key, name in config["alias"].items() if key in config["alias"]})

    return lf.unique()


def _column_start_by(schema: polars.Schema, start: str) -> list[str]:
    return [name for name in schema.names() if name.startswith(start)]


def extract_dataset_name(_lf: polars.LazyFrame, config: dict[str, typing.Any]) -> list[str]:
    """Extract list of dataset in LazyFrame."""
    return (
        _lf.select(config["alias"]["dataset"])
        .unique()
        .sort(config["alias"]["dataset"])
        .collect()
        .get_column(config["alias"]["dataset"])
        .to_list()
    )


def scan_chr_list(input_directory: pathlib.Path) -> typing.Iterator[str]:
    """Extract chromosome from input directory."""
    with os.scandir(input_directory) as dir_scan:
        for entry in dir_scan:
            if entry.is_file() and entry.name.endswith(".parquet") and entry.stat().st_size != 0:
                yield entry.name.split(".")[0]


def numeric_column(_lf: polars.LazyFrame) -> list[str]:
    """Generate plotable numeric value."""
    return [name for name, col_type in dict(_lf.collect_schema()).items() if col_type.is_numeric()]


def collect_and_sample(
    _lf: polars.LazyFrame,
    fraction: int,
) -> polars.DataFrame:
    """Sample a polars.LazyFrame and collect it in polars.DataFrame."""
    return _lf.collect().sample(fraction=fraction / 100)


def group_bar_chart(df: polars.DataFrame, value: str, color: str, column: str) -> altair.Chart:
    """Generate an altair bar chart."""
    selection = altair.selection_point(fields=[color], bind="legend")

    return (
        altair.Chart(df)
        .mark_bar()
        .encode(
            x=altair.X(color),
            y=altair.Y(value),
            color=altair.Color(color),
            column=altair.Column(column),
            opacity=altair.when(selection).then(altair.value(1)).otherwise(altair.value(0.1)),
        )
        .add_params(
            selection,
        )
    )


def scatter_chart(df: polars.DataFrame, x: str, y: str, color: str) -> altair.Chart:
    """Generate a scatter chart."""
    selection = altair.selection_point(fields=[color], bind="legend")

    return (
        altair.Chart(df)
        .mark_point(
            size=1,
            strokeWidth=1,
        )
        .encode(
            x=altair.X(x),
            y=altair.Y(y),
            color=altair.Color(color),
            opacity=altair.when(selection).then(altair.value(1)).otherwise(altair.value(0.1)),
        )
        .add_params(
            selection,
        )
    )


def line_chart(df: polars.DataFrame, x: str, y: str, color: str) -> altair.Chart:
    """Generate a line chart."""
    print(df)

    selection = altair.selection_point(fields=[color], bind="legend")

    return (
        altair.Chart(df)
        .mark_line()
        .encode(
            x=altair.X(x),
            y=altair.Y(y),
            color=altair.Color(color),
            opacity=altair.when(selection).then(altair.value(1)).otherwise(altair.value(0.1)),
        )
        .add_params(
            selection,
        )
    )
