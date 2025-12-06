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


def by_chr(input_path: pathlib.Path) -> None:
    """Principal function of by_chr page."""
    lf = polars.scan_parquet(input_path)

    dataset_name_selector = streamlit.sidebar.selectbox("dataset", vkd.streamlit.dataset_name(lf))
    chr_name_selector = streamlit.sidebar.selectbox("chromosome", vkd.streamlit.chr_list(lf))
    subsample_selector = streamlit.sidebar.slider("fraction of data show", min_value=1, max_value=100, value=1)
    column_selector = streamlit.sidebar.selectbox("value to show", vkd.streamlit.numeric_column(lf))

    df = vkd.streamlit.by_chr_filtering(lf, dataset_name_selector, chr_name_selector, subsample_selector)

    streamlit.title("Coverage by chromosome")
    streamlit.altair_chart(vkd.streamlit.cov_by_chr(df))

    streamlit.title("Violin Plot of value")
    streamlit.altair_chart(vkd.streamlit.violin_plot(df, column_selector))

    streamlit.title("Variant length")
    streamlit.altair_chart(vkd.streamlit.variant_length(df))
