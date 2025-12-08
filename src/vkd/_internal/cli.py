# Why does this file exist, and why not put this in `__main__`?
#
# You might be tempted to import things from `__main__` later,
# but that will cause problems: the code will get executed twice:
#
# - When you run `python -m vkd` python will execute
#   `__main__.py` as a script. That means there won't be any
#   `vkd.__main__` in `sys.modules`.
# - When you import `__main__` it will get executed again (as a module) because
#   there's no `vkd.__main__` in `sys.modules`.

# std import
from __future__ import annotations

import argparse
import importlib
import inspect
import logging
import os
import pathlib
import subprocess
import sys
import tempfile
import typing

# 3rd party import
import polars

from vkd import reader

# project import
from vkd._internal import debug


class _DebugInfo(argparse.Action):
    def __init__(self, nargs: int | str | None = 0, **kwargs: typing.Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> None:  # noqa: ARG002
        debug._print_debug_info()
        sys.exit(0)


def get_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser.

    Returns:
        An argparse parser.
    """
    parser = argparse.ArgumentParser(prog="vkd")
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {debug._get_version()}",
    )
    parser.add_argument(
        "--debug-info",
        action=_DebugInfo,
        help="Print debug information",
    )
    parser.add_argument(
        "--threads",
        type=int,
        help="Number of threads usable",
        default=1,
    )

    subparser = parser.add_subparsers()

    merge_parser = subparser.add_parser("merge", help=inspect.getdoc(merge))
    merge_parser.add_argument(
        "-n",
        "--name-dataset",
        type=str,
        help="Name of dataset",
        required=True,
        nargs="+",
    )
    merge_parser.add_argument(
        "-q",
        "--query-path",
        type=pathlib.Path,
        help="Path to query vcf",
        required=True,
        nargs="+",
    )
    merge_parser.add_argument(
        "-Q",
        "--query-path-labeled",
        type=pathlib.Path,
        help="Path to query vcf labeled",
        required=True,
        nargs="+",
    )
    merge_parser.add_argument(
        "-c",
        "--clinvar-path",
        type=pathlib.Path,
        help="Path to clinvar annotation",
        required=False,
    )
    merge_parser.add_argument(
        "-s",
        "--snpeff-path",
        type=pathlib.Path,
        help="Path to snpeff annotation",
        required=False,
        nargs="+",
    )
    merge_parser.add_argument(
        "-v",
        "--vep-path",
        type=pathlib.Path,
        help="Path to vep annotation",
        required=False,
        nargs="+",
    )
    merge_parser.add_argument(
        "-o",
        "--output-path",
        type=pathlib.Path,
        help="Path where to write result",
        required=True,
    )
    merge_parser.set_defaults(func=merge)

    serve_parser = subparser.add_parser(
        "serve",
        help="Start web server for data analysis",
    )
    serve_parser.add_argument(
        "-i",
        "--input-path",
        type=pathlib.Path,
        help="Result of merge data",
        required=True,
    )
    serve_parser.add_argument(
        "-c",
        "--config-path",
        type=pathlib.Path,
        help="Configuration path",
        required=True,
    )
    serve_parser.set_defaults(func=serve)

    return parser


def main(args: list[str] | None = None) -> int:
    """Run the main program.

    This function is executed when you type `vkd` or `python -m vkd`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    parser = get_parser()
    opts = parser.parse_args(args=args)

    os.environ["POLARS_MAX_THREADS"] = str(opts.threads)

    if "func" not in opts:
        parser.print_help(sys.stderr)
        return 0

    return opts.func(opts)


def merge(opts: argparse.Namespace) -> int:
    """Perform a merge of pipeline output."""
    logger = logging.getLogger("merge")
    lfs = []

    schema_global: dict[str, polars.DataType] | None = None

    snpeffs = [None] * len(opts.name_dataset) if opts.snpeff_path is None else opts.snpeff_path
    veps = [None] * len(opts.name_dataset) if opts.vep_path is None else opts.vep_path

    for name, query, label, snpeff, vep in zip(
        opts.name_dataset,
        opts.query_path,
        opts.query_path_labeled,
        snpeffs,
        veps,
    ):
        lf = reader.vcf2lazyframe(query)
        label_lf = reader.vcf2lazyframe(label).select(["chr", "position", "ref", "alt", "format_bd"])

        lf = lf.join(label_lf, on=["chr", "position", "ref", "alt"], how="left")

        if snpeff is not None:
            annot_lf = reader.vcf2lazyframe(snpeff).select(["chr", "position", "ref", "alt", "info_ANN"])
            annot_lf = reader.parse_info_ann(annot_lf, "snpeff")
            lf = lf.join(annot_lf, on=["chr", "position", "ref", "alt"], how="left")

        if vep is not None:
            annot_lf = reader.vcf2lazyframe(snpeff).select(["chr", "position", "ref", "alt", "info_ANN"])
            annot_lf = reader.parse_info_ann(annot_lf, "vep")
            lf = lf.join(annot_lf, on=["chr", "position", "ref", "alt"], how="left")

        lf = lf.with_columns(dataset=polars.lit(name))

        schema = lf.collect_schema()
        if schema_global is None:
            schema_global = dict(schema)
        else:
            for col, dtypes in schema.items():
                if col in schema_global and schema_global[col] != dtypes:
                    logger.info(f"drop {col} old dtypes {dtypes} new dtypes {schema_global[col]}")
                    del schema_global[col]

        lfs.append(lf)

    lf = polars.concat(lfs) if schema_global is None else polars.concat([lf.select(schema_global.keys()) for lf in lfs])

    if opts.clinvar_path is not None:
        clinvar_lf = reader.vcf2lazyframe(opts.clinvar_path, with_genotype=False)
        clinvar_lf = clinvar_lf.with_columns(chr=polars.col("chr").str.replace(r"^", "chr"))

        lf = lf.join(clinvar_lf, on=["chr", "position", "ref", "alt"], how="left")

    lf.sink_parquet(
        opts.output_path,
    )

    return 0


def serve(opts: argparse.Namespace) -> int:
    """Write a streamlit script in stdout."""
    if not importlib.util.find_spec("streamlit"):
        print("Reinstall vkd with web optional dependencies group to use serve command")
        return 1

    tmp_dir = tempfile.TemporaryDirectory()
    tmp_path = pathlib.Path(tmp_dir.name)

    enable_page = ["generic", "by_chr"]

    main_file_path = tmp_path / "main.py"
    with open(main_file_path, "w") as fh:
        print(
            f"""import vkd
import vkd.streamlit

vkd.streamlit.main({enable_page})
""",
            file=fh,
        )

    for page in enable_page:
        with open(tmp_path / f"{page}.py", "w") as fh:
            print(
                f"""import vkd
import vkd.streamlit
import vkd.streamlit.{page}

vkd.streamlit.{page}.{page}("{opts.input_path}", "{opts.config_path}")
""",
                file=fh,
            )

    subprocess.run(["streamlit", "run", main_file_path], check=True)  # noqa: S603 S607 we create main file content

    return 0
