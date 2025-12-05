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
import sys
import tempfile
import typing

# 3rd party import
import streamlit
import streamlit.web
import streamlit.web.bootstrap

# project import
from vkd._internal import debug
from vkd import reader


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
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {debug._get_version()}")
    parser.add_argument("--debug-info", action=_DebugInfo, help="Print debug information")
    parser.add_argument("--threads", type=int, help="Number of threads usable", default=1)

    subparser = parser.add_subparsers()

    merge_parser = subparser.add_parser("merge", help=inspect.getdoc(merge))
    merge_parser.add_argument("-t", "--truth-path", type=pathlib.Path, help="Path to truth vcf", required=True)
    merge_parser.add_argument("-q", "--query-path", type=pathlib.Path, help="Path to query vcf", required=True)
    merge_parser.add_argument("-s", "--summary-path", type=pathlib.Path, help="Path to summary statistic", required=True)
    merge_parser.add_argument(
        "-T", "--truth-path-labeled", type=pathlib.Path, help="Path to truth vcf labeled", required=True
    )
    merge_parser.add_argument(
        "-Q", "--query-path-labeled", type=pathlib.Path, help="Path to query vcf labeled", required=True
    )
    merge_parser.add_argument("-o", "--output-path", type=pathlib.Path, help="Path where to write result", required=True)
    merge_parser.set_defaults(func=merge)

    serve_parser = subparser.add_parser("serve", help="Start web server for data analysis")
    serve_parser.add_argument("-i", "--input-path", type=pathlib.Path, help="Result of merge data", required=True)
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
    truth_lf = reader.vcf2lazyframe(opts.truth_path)
    truth_label_lf = reader.vcf2lazyframe(opts.truth_path_labeled)
    truth_lf = truth_lf.join(truth_label_lf, on=["chr", "position", "ref", "alt"])

    query_lf = reader.vcf2lazyframe(opts.truth_path)
    query_label_lf = reader.vcf2lazyframe(opts.truth_path_labeled)
    query_lf = query_lf.join(query_label_lf, on=["chr", "position", "ref", "alt"])

    final = query_lf.join(truth_lf, on=["chr", "position", "ref", "alt"], suffix="_truth")

    final.sink_parquet(opts.output_path)

    return 0


def serve(opts: argparse.Namespace) -> int:
    """Write a streamlit script in stdout."""
    temp_dir = tempfile.TemporaryDirectory()
    temp_file_path = os.path.join(temp_dir.name, 'app.py')

    with open(temp_file_path, "w") as fh:
        print(f"""import vkd

vkd.streamlit.main("{opts.input_path}")
""", file=fh)

    streamlit.web.bootstrap.run(temp_file_path, False, [], [])

    return 0
