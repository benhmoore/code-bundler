"""Command line interface for the package."""

import argparse
import logging
import sys
from typing import List, Optional

from codebundler import __version__
from codebundler.core.combiner import combine_from_filelist, combine_source_files
from codebundler.core.tree import generate_tree_file, parse_tree_file
from codebundler.utils.helpers import InteractiveSetup

logger = logging.getLogger(__name__)


def setup_parser() -> argparse.ArgumentParser:
    """
    Set up the command line argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description=(
            "Combine source files with optional transformations. "
            "Can export or parse a 'tree file' for fine-grained selection."
        )
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"codebundler {__version__}",
        help="Show version information and exit.",
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in guided, interactive mode.",
    )

    # Possibly missing in interactive mode
    parser.add_argument(
        "source_dir", nargs="?", default=None, help="Directory to search."
    )
    parser.add_argument(
        "output_file", nargs="?", default=None, help="Output file path."
    )
    parser.add_argument("--ext", help="File extension (e.g., .py, .cs, .js, .php).")

    parser.add_argument(
        "--ignore-names", nargs="*", default=[], help="Partial filenames to ignore."
    )
    parser.add_argument(
        "--ignore-paths",
        nargs="*",
        default=[],
        help="Partial relative paths to ignore.",
    )
    parser.add_argument(
        "--include-names",
        nargs="*",
        default=[],
        help="Only include files whose names contain these keywords.",
    )

    parser.add_argument(
        "--strip-comments", action="store_true", help="Remove single-line comments."
    )
    parser.add_argument(
        "--no-strip-comments",
        action="store_false",
        dest="strip_comments",
        help="Don't remove single-line comments (override).",
    )

    parser.add_argument(
        "--remove-docstrings",
        action="store_true",
        help="Remove triple-quoted docstrings (Python only).",
    )
    parser.add_argument(
        "--no-remove-docstrings",
        action="store_false",
        dest="remove_docstrings",
        help="Don't remove docstrings (override).",
    )

    parser.add_argument(
        "--export-tree", help="Path to export a proposed tree (for manual editing)."
    )
    parser.add_argument("--use-tree", help="Path to an edited tree file to combine.")

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )

    # We want None as default so we can detect if user explicitly set these flags
    parser.set_defaults(strip_comments=None, remove_docstrings=None)

    return parser


def configure_logging(verbosity: int) -> None:
    """
    Configure logging based on verbosity level.

    Args:
        verbosity: Verbosity level (0=ERROR, 1=WARNING, 2=INFO, 3+=DEBUG)
    """
    log_levels = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG,
    }

    # Cap at level 3
    verbosity = min(verbosity, 3)

    # Configure root logger
    logging.basicConfig(
        level=log_levels[verbosity],
        format=(
            "%(levelname)s: %(message)s"
            if verbosity <= 1
            else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command line arguments (if None, sys.argv is used)

    Returns:
        Exit code
    """
    parser = setup_parser()
    parsed_args = parser.parse_args(args)

    # Setup logging first
    configure_logging(parsed_args.verbose)

    # ----------------------------------------------------
    # Handle exclusive flags first
    # ----------------------------------------------------
    if parsed_args.export_tree and parsed_args.use_tree:
        logger.error("Cannot use --export-tree and --use-tree at the same time.")
        return 1

    # ----------------------------------------------------
    # If we're using a tree, parse it NOW (before interactive)
    # ----------------------------------------------------
    filelist = []
    if parsed_args.use_tree:
        logger.info(f"Parsing tree file: {parsed_args.use_tree}")
        (
            tree_source_dir,
            tree_output_file,
            tree_extension,
            tree_strip_comments,
            tree_remove_docstrings,
            filelist,
        ) = parse_tree_file(parsed_args.use_tree)

        # Fill args from tree if missing on CLI
        if not parsed_args.source_dir and tree_source_dir:
            parsed_args.source_dir = tree_source_dir
            logger.debug(f"Using source directory from tree: {tree_source_dir}")

        if not parsed_args.output_file and tree_output_file:
            parsed_args.output_file = tree_output_file
            logger.debug(f"Using output file from tree: {tree_output_file}")

        # Also fill comment/docstring flags if still None
        if not parsed_args.ext and tree_extension:
            parsed_args.ext = tree_extension
            logger.debug(f"Using extension from tree: {tree_extension}")

        if parsed_args.strip_comments is None and tree_strip_comments is not None:
            parsed_args.strip_comments = tree_strip_comments
            logger.debug(
                f"Using strip_comments setting from tree: {tree_strip_comments}"
            )

        if parsed_args.remove_docstrings is None and tree_remove_docstrings is not None:
            parsed_args.remove_docstrings = tree_remove_docstrings
            logger.debug(
                f"Using remove_docstrings setting from tree: {tree_remove_docstrings}"
            )

    # ----------------------------------------------------
    # Possibly go interactive now (only if requested or no data)
    # ----------------------------------------------------
    # If user did not explicitly set --use-tree, or if we still
    # have missing arguments AND user asked for interactive mode, prompt them.
    # (If the user used --use-tree without --interactive and the tree file
    #  has all the data, we won't prompt.)
    needs_essential_args = (
        not parsed_args.source_dir or not parsed_args.output_file or not parsed_args.ext
    )
    if parsed_args.interactive or (needs_essential_args and not sys.stdin.isatty()):
        logger.info("Running in interactive mode")
        parsed_args = InteractiveSetup.run_interactive(parsed_args)

    # ----------------------------------------------------
    # 1) Export tree
    # ----------------------------------------------------
    if parsed_args.export_tree:
        logger.info(f"Exporting tree to {parsed_args.export_tree}")
        try:
            file_count = generate_tree_file(
                source_dir=parsed_args.source_dir,
                tree_output_path=parsed_args.export_tree,
                extension=parsed_args.ext,
                ignore_names=parsed_args.ignore_names,
                ignore_paths=parsed_args.ignore_paths,
                include_names=parsed_args.include_names,
                output_file=parsed_args.output_file,
                remove_comments=bool(parsed_args.strip_comments),
                remove_docstrings=bool(parsed_args.remove_docstrings),
            )
            logger.info(
                f"Exported tree with {file_count} matching files to {parsed_args.export_tree}. "
                f"Edit it, then re-run with --use-tree."
            )
            return 0
        except Exception as e:
            logger.error(f"Error exporting tree: {e}")
            return 1

    # ----------------------------------------------------
    # 2) Use tree (already parsed)
    # ----------------------------------------------------
    if parsed_args.use_tree:
        # Check for missing info
        if not parsed_args.source_dir:
            logger.error("No source directory provided (and none found in the tree).")
            return 1
        if not parsed_args.output_file:
            logger.error("No output file provided (and none found in the tree).")
            return 1
        if not parsed_args.ext:
            logger.error("No extension provided (and none found in the tree).")
            return 1
        if not filelist:
            logger.warning("No valid file paths found in the tree file.")
            return 0

        logger.info(
            f"Combining files from tree {parsed_args.use_tree} into {parsed_args.output_file}"
        )
        try:
            processed_count = combine_from_filelist(
                source_dir=parsed_args.source_dir,
                output_file=parsed_args.output_file,
                extension=parsed_args.ext,
                filelist=filelist,
                remove_comments=bool(parsed_args.strip_comments),
                remove_docstrings=bool(parsed_args.remove_docstrings),
            )
            logger.info(
                f"Combined {processed_count} files into '{parsed_args.output_file}' from tree '{parsed_args.use_tree}'."
            )
            return 0
        except Exception as e:
            logger.error(f"Error combining files from tree: {e}")
            return 1

    # ----------------------------------------------------
    # 3) Direct combine (no tree)
    # ----------------------------------------------------
    if not parsed_args.source_dir:
        logger.error("No source_dir provided.")
        return 1
    if not parsed_args.output_file:
        logger.error("No output_file provided.")
        return 1
    if not parsed_args.ext:
        logger.error("No extension provided.")
        return 1

    logger.info(
        f"Directly combining files from {parsed_args.source_dir} into {parsed_args.output_file}"
    )
    try:
        processed_count = combine_source_files(
            source_dir=parsed_args.source_dir,
            output_file=parsed_args.output_file,
            extension=parsed_args.ext,
            ignore_names=parsed_args.ignore_names,
            ignore_paths=parsed_args.ignore_paths,
            include_names=parsed_args.include_names,
            remove_comments=bool(parsed_args.strip_comments),
            remove_docstrings=bool(parsed_args.remove_docstrings),
        )
        logger.info(
            f"Directly combined {processed_count} files into '{parsed_args.output_file}'."
        )
        return 0
    except Exception as e:
        logger.error(f"Error combining files directly: {e}")
        return 1
