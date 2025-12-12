"""vkd module that generate generic streamlit page."""

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


def generic(input_directory: pathlib.Path, config_path: pathlib.Path) -> None:
    """Principal function of generic page.

    Aggregate generic information.
    """
    config = vkd.streamlit.read_config(config_path)

    lf = polars.concat(
        [
            vkd.streamlit.read_parquet(input_directory, chr_name, config)
            for chr_name in vkd.streamlit.scan_chr_list(input_directory)
        ],
    )

    # Define sidebar selector
    streamlit.title("Repartition of variant by chromosome and label.")
    streamlit.altair_chart(
        vkd.streamlit.group_bar_chart(
            __counts(lf, [config["alias"]["chr"], config["alias"]["format_bd"], config["alias"]["dataset"]]),
            "len",
            config["alias"]["format_bd"],
            config["alias"]["dataset"],
        ),
    )

    streamlit.title("Variant common between dataset.")


@streamlit.cache_data
def __counts(_lf: polars.LazyFrame, columns: list[str]) -> polars.DataFrame:
    """Run a group by and count element."""
    return _lf.group_by(columns).len().collect()
