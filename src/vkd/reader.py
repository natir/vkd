"""vkd reader definition."""

# std import
from __future__ import annotations

import collections
import re
import typing

# 3rd party import
import polars
import xopen

# project import


if typing.TYPE_CHECKING:
    # std import
    import pathlib


def vcf2lazyframe(path: pathlib.Path) -> polars.LazyFrame:
    """Parse vcf information of input and generate a polars.LazyFrame."""
    lf = polars.scan_csv(
        path,
        new_columns=[
            "chr",
            "position",
            "_id",
            "ref",
            "alt",
            "qual",
            "filter",
            "_info",
            "_format",
            "genotype",
        ],
        separator="\t",
        comment_prefix="#",
        has_header=False,
        null_values=["."],
    )

    formats = dict(_lazyframe2format_pos(lf))

    bad_column_parsing = _parse_vcf_header(path, formats)

    lf = lf.with_columns(
        bad_column_parsing["info"],
    )

    lf = polars.concat(
        [
            lf.filter(polars.col("_format") == format_str).with_columns(
                bad_column_parsing[format_str],
            )
            for format_str in formats
        ],
    )

    lf = lf.drop("_id", "_info", "_format", "genotype")

    return lf


def _lazyframe2format_pos(
    lf: polars.LazyFrame,
) -> typing.Iterator[tuple[str, dict[str, int]]]:
    """Create a dictionary of format element associate with position in format string."""
    for format_str in lf.select("_format").unique().collect().get_column("_format").to_list():
        yield (format_str, {k: v for v, k in enumerate(format_str.split(":"))})


def _parse_vcf_header(
    path: pathlib.Path,
    formats: dict[str, dict[str, int]],
) -> dict[str, list[polars.Expr]]:
    """Read a vcf header to generate a list of polars expression to extract info and genotype field.

    Args:
        path: Path to vcf file
        formats: All format string present in vcf file

    Return:
        Set of expression associate to set of data should be parsed.
    """
    category2expression: dict[str, list[polars.Expr]] = collections.defaultdict(list)

    with xopen.xopen(path) as fh:
        for line in fh:
            if line.startswith("#CHR"):
                break
            if line.startswith("##INFO="):
                if (expr := _parse_info_line(line)) is not None:
                    category2expression["info"].append(expr)
            elif line.startswith("##FORMAT="):
                for format_str, format_pos in formats.items():
                    if (expr := _parse_format_line(line, format_pos)) is not None:
                        category2expression[format_str].append(expr)

    return category2expression


INFO_RE: typing.Pattern = re.compile(
    r"ID=(?P<id>([A-Za-z_][0-9A-Za-z_.]*|1000G)),Number=(?P<number>[ARG0-9\.]+),Type=(?P<type>Integer|Float|String|Character)",
)


def _parse_info_line(line: str) -> polars.Expr | None:
    """Parse vcf header info line to generate polars.Expr."""
    if search := INFO_RE.search(line):
        name = search["id"]
        number = search["number"]
        format_type = search["type"]

        regex = rf"{name}=([^;]+);?"

        local_expr = polars.col("_info").str.extract(regex, 1)

        if number == "1":
            if format_type == "Integer":
                local_expr = local_expr.cast(polars.Int64)
            elif format_type == "Float":
                local_expr = local_expr.cast(polars.Float64)
            elif format_type in {"String", "Character"}:
                pass  # Not do anything on string or character
            else:
                pass  # Not reachable
        else:
            local_expr = local_expr.str.split(",")
            if format_type == "Integer":
                local_expr = local_expr.cast(polars.List(polars.Int64))
            elif format_type == "Float":
                local_expr = local_expr.cast(polars.List(polars.Float64))
            elif format_type in {"String", "Character"}:
                pass  # Not do anything on string or character
            else:
                pass  # Not reachable

        return local_expr.alias(f"info_{name}")

    return None


FORMAT_RE: typing.Pattern = re.compile(
    "ID=(?P<id>[A-Za-z_][0-9A-Za-z_.]*),Number=(?P<number>[ARG0-9\\.]+),Type=(?P<type>Integer|Float|String|Character)",
)


def _parse_format_line(line: str, format_pos: dict[str, int]) -> polars.Expr | None:
    """Parse vcf header info line to generate polars.Expr."""
    if search := FORMAT_RE.search(line):
        name = search["id"]
        number = search["number"]
        format_type = search["type"]

        if name in format_pos:
            local_expr = polars.col("genotype").str.split(":").list.get(format_pos[name], null_on_oob=True)
        else:
            local_expr = polars.lit("").str.split(":").list.get(0, null_on_oob=True)

        if number == "1":
            if format_type == "Integer":
                local_expr = local_expr.str.to_integer(base=10, strict=False).cast(
                    polars.UInt32,
                )
            elif format_type == "Float":
                local_expr = local_expr.str.to_decimal(scale=40).cast(polars.Float32)
            elif format_type in {"String", "Character"}:
                pass  # Nothing to do for string and character
            else:
                pass  # Not reachable
        else:
            local_expr = local_expr.str.split(",")
            if format_type == "Integer":
                local_expr = local_expr.list.eval(
                    polars.element().str.to_integer(base=10, strict=False).cast(polars.UInt32),
                )
            elif format_type == "Float":
                local_expr = local_expr.list.eval(
                    polars.element().str.to_decimal(scale=40).cast(polars.Float32),
                )
            elif format_type in {"String", "Character"}:
                pass  # Nothing to do for string and character
            else:
                pass  # Not reachable

        return local_expr.alias(f"format_{name.lower()}")

    return None
