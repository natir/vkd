"""vkd module that generate generic streamlit page."""

# std import
from __future__ import annotations

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


def annotation(input_directory: pathlib.Path, config_path: pathlib.Path) -> None:
    """Show information related to variant status and annotation."""
    config = vkd.streamlit.read_config(config_path)

    chromosome_selector = streamlit.sidebar.selectbox("chromsome", vkd.streamlit.chr_list(input_directory))

    lf = polars.scan_parquet(input_directory / f"{chromosome_selector}.parquet")
    schema = lf.collect_schema()

    dataset_name_selector = streamlit.sidebar.selectbox("dataset", vkd.streamlit.dataset_name(lf))
    lf = lf.filter(polars.col("dataset") == dataset_name_selector)

    annotator_selector = streamlit.sidebar.selectbox("annotator", _variant_annotator(schema))
    lf = lf.select(config["select_column"] + vkd.streamlit._column_start_by(schema, annotator_selector))

    group = lf.collect().group_by(["format_bd", f"{annotator_selector}_impact"]).len()
    streamlit.title("Variant type repartition")
    streamlit.altair_chart(
        altair.Chart(group)
        .mark_point()
        .encode(
            altair.X(f"{annotator_selector}_impact"),
            altair.Y("len").scale(type="log"),
            altair.Color("format_bd"),
        ),
    )

    df = lf.with_columns(
        format_bd=polars.concat_str("format_bd", f"{annotator_selector}_impact", separator="_"),
    ).collect()
    streamlit.title("Violin Plot of a specific column")
    column_selector = streamlit.selectbox(
        "Column to show",
        schema.names(),
    )
    streamlit.altair_chart(vkd.streamlit.violin_plot(df, config, column_selector))


def _variant_annotator(schema: polars.Schema) -> list[str]:
    """Get variant annotator present in dataset."""
    annotator = []

    if "snpeff_effect" in schema:
        annotator.append("snpeff")

    if "vep_effect" in schema:
        annotator.append("vep")

    return annotator
