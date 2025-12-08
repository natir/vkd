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


def vcf2lazyframe(path: pathlib.Path, *, with_genotype: bool = True) -> polars.LazyFrame:
    """Parse vcf information of input and generate a polars.LazyFrame."""
    new_columns = [
        "chr",
        "position",
        "_id",
        "ref",
        "alt",
        "qual",
        "filter",
        "_info",
    ]

    if with_genotype:
        new_columns.extend(["_format", "genotype"])

    lf = polars.scan_csv(
        path,
        comment_prefix="#",
        has_header=False,
        new_columns=new_columns,
        null_values=["."],
        schema_overrides={"chr": polars.String},
        separator="\t",
    )

    formats = dict(_lazyframe2format_pos(lf)) if with_genotype else {}

    bad_column_parsing = _parse_vcf_header(path, formats)

    lf = lf.with_columns(
        bad_column_parsing["info"],
    )

    if with_genotype:
        lf = polars.concat(
            [
                lf.filter(polars.col("_format") == format_str).with_columns(
                    bad_column_parsing[format_str],
                )
                for format_str in formats
            ],
        )

    lf = lf.drop("_id", "_info")
    if with_genotype:
        lf = lf.drop("_format", "genotype")

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


def parse_info_ann(lf: polars.LazyFrame, prefix: str) -> polars.LazyFrame:
    """Extract information if info_ANN column."""
    lf = lf.explode("info_ANN")

    lf = lf.with_columns(
        ann=polars.col("info_ANN").str.split("|").cast(polars.List(polars.Utf8())),
    ).drop("info_ANN")

    lf = lf.with_columns(
        [
            polars.col("ann").list.get(1).alias(f"{prefix}_effect"),
            polars.col("ann").list.get(2).alias(f"{prefix}_impact"),
            polars.col("ann").list.get(3).alias(f"{prefix}_gene"),
            polars.col("ann").list.get(4).alias(f"{prefix}_geneid"),
            polars.col("ann").list.get(5).alias(f"{prefix}_feature"),
            polars.col("ann").list.get(6).alias(f"{prefix}_feature_id"),
            polars.col("ann").list.get(7).alias(f"{prefix}_bio_type"),
            polars.col("ann").list.get(8).alias(f"{prefix}_rank"),
            polars.col("ann").list.get(9).alias(f"{prefix}_hgvs_c"),
            polars.col("ann").list.get(10).alias(f"{prefix}_hgvs_p"),
            polars.col("ann").list.get(11).alias(f"{prefix}_cdna_pos"),
            polars.col("ann").list.get(12).alias(f"{prefix}_cdna_len"),
            polars.col("ann").list.get(13).alias(f"{prefix}_cds_pos"),
            polars.col("ann").list.get(14).alias(f"{prefix}_cds_len"),
            polars.col("ann").list.get(15).alias(f"{prefix}_aa_pos"),
        ],
    )

    return lf.drop("ann")
