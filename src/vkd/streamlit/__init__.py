"""vkd module that generate streamlit interface."""

# std import
from __future__ import annotations

# 3rd party import
import altair
import polars
import streamlit

# project import


def main() -> None:
    """Streamlit main page."""
    altair.data_transformers.disable_max_rows()

    pages = streamlit.navigation([streamlit.Page("generic.py"), streamlit.Page("by_chr.py")])

    pages.run()


def dataset_name(_lf: polars.LazyFrame) -> list[str]:
    """Extract list of dataset in LazyFrame."""
    return _lf.select("dataset").unique().sort("dataset").collect().get_column("dataset").to_list()


def chr_list(_lf: polars.LazyFrame) -> list[str]:
    """Extract chromosome list from LazyFrame."""
    return (
        _lf.select("chr")
        .unique()
        .sort(polars.col("chr").str.extract(r"(\d+)").cast(polars.Int32()))
        .collect()
        .get_column("chr")
        .to_list()
    )


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
def by_chr_filtering(_lf: polars.LazyFrame, dataset: str, chr_name: str, fraction: int) -> polars.DataFrame:
    """Filter data in LazyFrame and collect it in dataframe."""
    return (
        _lf.filter(polars.col("chr") == chr_name)
        .filter(polars.col("dataset") == dataset)
        .collect()
        .sample(fraction=fraction / 100)
    )


@streamlit.cache_data
def cov_by_chr(df: polars.DataFrame) -> altair.Chart:
    """Generate plot coverage of each variant."""
    df = df.select("position", "format_dp", "format_bd")
    return (
        altair.Chart(df)
        .mark_point(shape="circle", filled=True, size=10)
        .encode(
            x=altair.X("position"),
            y=altair.Y("format_dp"),
            color=altair.Color("format_bd"),
        )
    )


@streamlit.cache_data
def violin_plot(df: polars.DataFrame, column: str) -> altair.Chart:
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
            .axis(labels=False, values=[0], grid=False, ticks=True),
            altair.Y(column),
            altair.Color("format_bd"),
            altair.Column("format_bd").spacing(0).header(titleOrient="bottom", labelOrient="bottom", labelPadding=0),
        )
        .configure_view(
            stroke=None,
        )
    )


@streamlit.cache_data
def variant_length(df: polars.DataFrame) -> altair.Chart:
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
            altair.Y("len").scale(type="log"),
            altair.Color("format_bd"),
        )
    )
