"""vkd module that generate generic streamlit page."""

# std import
from __future__ import annotations

import typing

import altair_upset

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
    df = __upset_data(
        lf,
        [config["alias"]["chr"], config["alias"]["position"], config["alias"]["ref"], config["alias"]["alt"]],
        config["alias"]["dataset"],
    )
    df_pandas = df.to_pandas()
    chart = altair_upset.UpSetAltair(
        data=df_pandas,
        sets=df_pandas.columns.tolist(),
    ).chart

    chart.save("test.html")
    streamlit.altair_chart(chart)


@streamlit.cache_data
def __counts(_lf: polars.LazyFrame, columns: list[str]) -> polars.DataFrame:
    """Run a group by and count element."""
    return _lf.group_by(columns).len().collect()


@streamlit.cache_data
def __upset_data(_lf: polars.LazyFrame, match_row: list[str], set_column: str) -> polars.DataFrame:
    """Ru ."""
    lf = _lf.select(*match_row, set_column)
    df = lf.collect()
    set_values = df.get_column(set_column).unique().to_list()
    df = df.pivot(on=set_column, index=match_row, values=set_column)
    df = df.with_columns(
        [polars.col(name).is_null().alias(name).cast(polars.Int8) for name in set_values],
    )
    df = df.drop(*match_row)
    return df.rename({col_name: col_name.replace(".", "") for col_name in df.columns})
