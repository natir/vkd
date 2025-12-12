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

    annotator_selector = streamlit.sidebar.selectbox(
        "annotator",
        _variant_annotator(df.schema),
    )
    df = df.select([config["alias"][name] for name in config["select_column"]])

    group = df.group_by(
        [config["alias"]["format_bd"], f"{annotator_selector}_impact"],
    ).len()
    streamlit.title("Variant type repartition")
    streamlit.altair_chart(
        altair.Chart(group)
        .mark_point()
        .encode(
            altair.X(f"{annotator_selector}_impact"),
            altair.Y("len").scale(type="log"),
            altair.Color(config["alias"]["format_bd"]),
        ),
    )

    df = lf.with_columns(
        format_bd=polars.concat_str(
            config["alias"]["format_bd"],
            f"{annotator_selector}_impact",
            separator="_",
        ),
    ).collect()
    streamlit.title("Violin Plot of a specific column")
    column_selector = streamlit.selectbox(
        "Column to show",
        vkd.streamlit.numeric_column(lf),
    )
    plot = vkd.streamlit.violin_chart(
        vkd.streamlit.one_column(
            df,
            column_selector,
            [config["alias"][f"{annotator_selector}_impact"]],
        ),
        column_selector,
        config["alias"][f"{annotator_selector}_impact"],
    )
    streamlit.altair_chart(
        plot,
    )


def _variant_annotator(schema: polars.Schema) -> list[str]:
    """Get variant annotator present in dataset."""
    annotator = []

    if "snpeff_effect" in schema:
        annotator.append("snpeff")

    if "vep_effect" in schema:
        annotator.append("vep")

    return annotator
