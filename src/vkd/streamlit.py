"""vkd module that generate streamlit interface."""

# std import
from __future__ import annotations

import pathlib

# 3rd party import
import altair
import polars
import streamlit

# project import


def main(input_path: pathlib.path) -> None:
    """Streamlit interface."""
    altair.data_transformers.disable_max_rows()

    lf = polars.scan_parquet(input_path)

    chr_name = streamlit.sidebar.selectbox("chromosome", chr_list(lf))
    subsample = streamlit.sidebar.slider("fraction of data show", min_value=1, max_value=100, value=1)
    point_size = streamlit.sidebar.slider("point_size", min_value=1, max_value=100)
    column = streamlit.sidebar.selectbox("value to show", numeric_column(lf))

    streamlit.title("Coverage by chromosome")
    df = cov_by_chr(lf, chr_name).sample(fraction=subsample/100)
    streamlit.text(f"number of row {df.height}")
    streamlit.scatter_chart(df, x="position", y="format_dp", color="format_bd", size=point_size)

    streamlit.title("Violin Plot of value")

    streamlit.altair_chart(violin_plot(lf, chr_name, column))


@streamlit.cache_data
def chr_list(_lf: polars.LazyFrame) -> list[str]:
    """Extract chromosome list from LazyFrame."""
    return _lf.select("chr").unique().sort("chr").collect().get_column("chr").to_list()


@streamlit.cache_data
def filter_by_chr(_lf: polars.LazyFrame, chr_name: str) -> polars.DataFrame:
    """Extract data of lazyframe."""
    return _lf.filter(polars.col("chr") == chr_name).collect()


@streamlit.cache_data
def cov_by_chr(_lf: polars.LazyFrame, chr_name: str) -> polars.DataFrame:
    """Generate a polars DataFrame with coverage by chromosome."""
    df = filter_by_chr(_lf, chr_name)
    df = df.select("position", "format_dp", "format_bd")

    return df


@streamlit.cache_data
def numeric_column(_lf: polars.LazyFrame) -> list[str]:
    """Generate plotable numeric value."""
    return [
        name for name, col_type in dict(_lf.collect_schema()).items()
        if col_type in [
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
                polars.UInt64
        ]
    ]

@streamlit.cache_data
def violin_plot(_lf: polars.LazyFrame, chr_name: str, column: str) -> altair.Chart:
    """Generate a violin plot of selected column."""
    df = filter_by_chr(_lf, chr_name)
    df = df.select(column, "format_bd")

    return altair.Chart(df).transform_density(
        column,
        as_=[column, "density"],
        groupby=["format_bd"]
    ).mark_area(orient='horizontal').encode(
        altair.X("density:Q")
        .stack('center')
        .impute(None)
        .title(None)
        .axis(labels=False, values=[0], grid=False, ticks=True),
        altair.Y(column),
        altair.Color("format_bd"),
        altair.Column("format_bd")
        .spacing(0)
        .header(titleOrient='bottom', labelOrient='bottom', labelPadding=0)
    ).configure_view(
        stroke=None
    )
