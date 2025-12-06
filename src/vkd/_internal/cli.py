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
import inspect
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
        "-t",
        "--truth-path",
        type=pathlib.Path,
        help="Path to truth vcf",
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
        "-T",
        "--truth-path-labeled",
        type=pathlib.Path,
        help="Path to truth vcf labeled",
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

    return opts.func(opts)


def merge(opts: argparse.Namespace) -> int:
    """Perform a merge of pipeline output."""
    lfs = []
    for name, truth, truth_label, query, query_label in zip(
        opts.name_dataset,
        opts.truth_path,
        opts.truth_path_labeled,
        opts.query_path,
        opts.truth_path_labeled,
    ):
        truth_lf = reader.vcf2lazyframe(truth)
        truth_label_lf = reader.vcf2lazyframe(truth_label).with_columns(
            dataset=polars.lit(name),
        )
        truth_lf = truth_lf.join(truth_label_lf, on=["chr", "position", "ref", "alt"])

        query_lf = reader.vcf2lazyframe(query)
        query_label_lf = reader.vcf2lazyframe(query_label).with_columns(
            dataset=polars.lit(name),
        )
        query_lf = query_lf.join(query_label_lf, on=["chr", "position", "ref", "alt"])

        final = query_lf.join(
            truth_lf,
            on=["chr", "position", "ref", "alt"],
            suffix="_truth",
        ).with_columns(dataset=polars.lit(name))

        lfs.append(final)

    polars.concat(lfs).sink_parquet(opts.output_path)

    return 0


def serve(opts: argparse.Namespace) -> int:
    """Write a streamlit script in stdout."""
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_path = pathlib.Path(tmp_dir.name)

    main_file_path = tmp_path / "main.py"
    with open(main_file_path, "w") as fh:
        print(
            """import vkd
import vkd.streamlit

vkd.streamlit.main()
""",
            file=fh,
        )

    enable_page = ["generic", "by_chr"]
    for page in enable_page:
        with open(tmp_path / f"{page}.py", "w") as fh:
            print(
                f"""import vkd
import vkd.streamlit
import vkd.streamlit.{page}

vkd.streamlit.{page}.{page}("{opts.input_path}")
""",
                file=fh,
            )

    subprocess.run(["streamlit", "run", main_file_path], check=True)  # noqa: S603 S607 we create main file content

    return 0
