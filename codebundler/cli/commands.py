"""Command line interface for the package."""

import argparse
import logging
import os
import sys
import time
from typing import List, Optional

from rich.table import Table

from codebundler import __version__
from codebundler.core.combiner import combine_source_files
from codebundler.utils.helpers import (
    console,
    create_panel,
    display_summary,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)


class RichLogHandler(logging.Handler):
    """Custom log handler that uses Rich for formatting."""

    def emit(self, record):
        level_styles = {
            logging.DEBUG: "[cyan]DEBUG:[/cyan]",
            logging.INFO: "[green]INFO:[/green]",
            logging.WARNING: "[yellow]WARNING:[/yellow]",
            logging.ERROR: "[red]ERROR:[/red]",
            logging.CRITICAL: "[bold red]CRITICAL:[/bold red]",
        }

        level_prefix = level_styles.get(
            record.levelno, f"[bold]LEVEL {record.levelno}:[/bold]"
        )

        # Format the message based on the log level
        if record.levelno >= logging.ERROR:
            console.print(f"{level_prefix} {record.getMessage()}", style="red")
        elif record.levelno >= logging.WARNING:
            console.print(f"{level_prefix} {record.getMessage()}", style="yellow")
        elif record.levelno >= logging.INFO:
            console.print(f"{level_prefix} {record.getMessage()}")
        else:  # DEBUG level
            # Include more details for debug messages
            module_part = f"[dim]{record.name}[/dim]" if hasattr(record, "name") else ""
            console.print(f"{level_prefix} {module_part} {record.getMessage()}")


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
        format="%(message)s",
        handlers=[RichLogHandler()],
    )

    # Set the log level for third-party libraries to WARNING unless in debug mode
    if verbosity < 3:
        for logger_name in logging.root.manager.loggerDict:
            if not logger_name.startswith("codebundler"):
                logging.getLogger(logger_name).setLevel(logging.WARNING)


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

    # Group commands by category for better help display
    info_group = parser.add_argument_group("Information")
    mode_group = parser.add_argument_group("Operation Modes")
    basic_group = parser.add_argument_group("Basic Options")
    filter_group = parser.add_argument_group("Filtering Options")
    transform_group = parser.add_argument_group("Transformation Options")
    output_group = parser.add_argument_group("Output Options")

    # Information options
    info_group.add_argument(
        "--version",
        action="version",
        version=f"codebundler {__version__}",
        help="Show version information and exit.",
    )

    # TUI mode options
    tui_group = parser.add_argument_group("TUI Options")
    
    tui_group.add_argument(
        "--hide-patterns",
        nargs="*",
        metavar="PATTERN",
        default=[],
        help="Glob patterns to hide from tree view (e.g. __pycache__/, *.meta).",
    )
    
    tui_group.add_argument(
        "--select-patterns",
        nargs="*",
        metavar="PATTERN",
        default=[],
        help="Glob patterns for initial file selection in the tree (e.g. *.py, docs/*.md).",
    )
    
    tui_group.add_argument(
        "--confirm-selection",
        action="store_true",
        default=True,
        help="Require user confirmation in the TUI before initial bundle/watch (default: True).",
    )
    
    tui_group.add_argument(
        "--no-confirm-selection",
        action="store_false",
        dest="confirm_selection",
        help="Start bundling immediately without confirmation in TUI mode.",
    )
    
    # TUI mode - primary mode of operation
    mode_group.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        dest="watch",
        help="Run in TUI mode (alias for --watch).",
    )

    # Tree-based functionality has been removed in favor of the TUI

    # Basic options (now with required flags)
    basic_group.add_argument(
        "--watch-path", 
        dest="source_dir",
        default=None, 
        help="Directory to search/watch (previously 'source_dir')."
    )

    basic_group.add_argument(
        "--output", 
        dest="output_file",
        default=None, 
        help="Output file path (previously 'output_file')."
    )

    basic_group.add_argument(
        "--ext", metavar="EXT", help="File extension (e.g., .py, .cs, .js, .php)."
    )

    # Filtering options
    filter_group.add_argument(
        "--ignore-names",
        nargs="*",
        metavar="KEYWORD",
        default=[],
        help="Partial filenames to ignore.",
    )

    filter_group.add_argument(
        "--ignore-paths",
        nargs="*",
        metavar="PATH",
        default=[],
        help="Partial relative paths to ignore.",
    )

    filter_group.add_argument(
        "--include-names",
        nargs="*",
        metavar="KEYWORD",
        default=[],
        help="Only include files whose names contain these keywords.",
    )

    filter_group.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Search directories recursively (default: True).",
    )

    filter_group.add_argument(
        "--no-recursive",
        action="store_false",
        dest="recursive",
        help="Don't search directories recursively.",
    )

    # Transformation options
    transform_group.add_argument(
        "--strip-comments", action="store_true", help="Remove single-line comments."
    )

    transform_group.add_argument(
        "--no-strip-comments",
        action="store_false",
        dest="strip_comments",
        help="Don't remove single-line comments (override).",
    )

    transform_group.add_argument(
        "--remove-docstrings",
        action="store_true",
        help="Remove triple-quoted docstrings (Python only).",
    )

    transform_group.add_argument(
        "--no-remove-docstrings",
        action="store_false",
        dest="remove_docstrings",
        help="Don't remove docstrings (override).",
    )

    # Output options
    output_group.add_argument(
        "--print-tree",
        action="store_true",
        help="Print the directory tree to the console.",
    )

    output_group.add_argument(
        "--format",
        choices=["default", "condensed", "expanded"],
        default="default",
        help="Output format style (default: default).",
    )

    output_group.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )

    output_group.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output."
    )

    output_group.add_argument(
        "--watch",
        action="store_true",
        help="Launch the interactive TUI (primary interface) for file selection and real-time updates.",
    )

    # We want None as default so we can detect if user explicitly set these flags
    parser.set_defaults(strip_comments=None, remove_docstrings=None)

    return parser


def display_welcome_banner() -> None:
    """Display a welcome banner when the application starts."""
    # Create a table for the header
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(justify="left", width=os.get_terminal_size().columns - 4)

    # Add a fancy ASCII art banner
    table.add_row(f"[bold cyan]{'='*30}[/bold cyan]")
    table.add_row(f"[bold cyan]CODE BUNDLER[/bold cyan]")
    table.add_row(f"[cyan]{'-'*30}[/cyan]")
    table.add_row(f"[dim]Combine and transform source code for LLM usage[/dim]")
    table.add_row(f"[dim]Version {__version__} | MIT License | Author: Ben Moore[/dim]")
    table.add_row(f"[bold cyan]{'='*30}[/bold cyan]")

    console.print()
    console.print(table)
    console.print()


def setup_tui_mode(parsed_args):
    """
    Set up and launch the TUI (Text User Interface) for interactive file selection.

    Args:
        parsed_args: Command line arguments

    Returns:
        Exit code
    """
    try:
        # Check for required arguments
        if not parsed_args.source_dir:
            print_error("No source directory (--watch-path) provided.")
            return 1
        if not parsed_args.output_file:
            print_error("No output file (--output) provided.")
            return 1
        if not parsed_args.ext:
            print_error("No extension provided.")
            return 1

        # Import the TUI app
        try:
            from codebundler.tui.app import CodeBundlerApp
        except ImportError as e:
            print_error(
                f"Error importing TUI modules: {e}\n"
                "Make sure all dependencies are installed: pip install codebundler[tui]"
            )
            return 1

        print_info("Launching TUI mode...")
        
        # Start the TUI application
        app = CodeBundlerApp(
            watch_path=parsed_args.source_dir,
            output_file=parsed_args.output_file,
            extension=parsed_args.ext,
            hide_patterns=parsed_args.hide_patterns,
            select_patterns=parsed_args.select_patterns,
            ignore_names=parsed_args.ignore_names,
            ignore_paths=parsed_args.ignore_paths,
            include_names=parsed_args.include_names,
            strip_comments=bool(parsed_args.strip_comments),
            remove_docstrings=bool(parsed_args.remove_docstrings),
            confirm_selection=parsed_args.confirm_selection,
        )
        
        app.run()
        return 0

    except Exception as e:
        print_error(f"Error setting up TUI mode: {e}")
        logger.error("Detailed error:", exc_info=True)
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        args: Command line arguments (if None, sys.argv is used)

    Returns:
        Exit code
    """
    try:
        # Parse arguments
        parser = setup_parser()
        parsed_args = parser.parse_args(args)

        # Setup logging first
        configure_logging(parsed_args.verbose)

        # Display welcome banner (if not in quiet mode)
        if parsed_args.verbose >= 0:
            display_welcome_banner()

        # Tree functionality has been removed in favor of the TUI

        # Check for required arguments if not in watch/TUI mode
        needs_essential_args = (
            not parsed_args.source_dir
            or not parsed_args.output_file
            or not parsed_args.ext
        )
        
        # If watch mode (TUI) is enabled, launch it
        if parsed_args.watch:
            if needs_essential_args:
                print_error("Missing required arguments for TUI mode:")
                if not parsed_args.source_dir:
                    print_error("  --watch-path: Source directory is required")
                if not parsed_args.output_file:
                    print_error("  --output: Output file path is required")
                if not parsed_args.ext:
                    print_error("  --ext: File extension is required")
                return 1
            return setup_tui_mode(parsed_args)

        # Old tree-based functionality has been removed in favor of the TUI

        # ----------------------------------------------------
        # 3) Direct combine (no tree)
        # ----------------------------------------------------
        if not parsed_args.source_dir:
            print_error("No source_dir provided.")
            return 1
        if not parsed_args.output_file:
            print_error("No output_file provided.")
            return 1
        if not parsed_args.ext:
            print_error("No extension provided.")
            return 1

        console.print(
            create_panel(
                "Direct Combine Mode",
                f"[bold]Source:[/bold] {parsed_args.source_dir}\n"
                f"[bold]Output:[/bold] {parsed_args.output_file}\n"
                f"[bold]Extension:[/bold] {parsed_args.ext}\n"
                f"[bold]Strip Comments:[/bold] {'Yes' if parsed_args.strip_comments else 'No'}\n"
                f"[bold]Remove Docstrings:[/bold] {'Yes' if parsed_args.remove_docstrings else 'No'}",
                "green",
            )
        )

        try:
            # Simple status message instead of progress bar
            with console.status(
                "[cyan]Scanning directory and combining files...[/cyan]"
            ):
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

            print_success(
                f"Combined {processed_count} files into '{parsed_args.output_file}'."
            )

            # Display stats
            total_lines = 0
            total_size = 0
            try:
                with open(parsed_args.output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    total_lines = content.count("\n") + 1
                    total_size = len(content)
            except Exception:
                pass

            display_summary(
                "Output Statistics",
                [
                    ("Files Processed", processed_count),
                    ("Total Lines", total_lines),
                    ("File Size", f"{total_size/1024:.1f} KB"),
                    ("Output File", parsed_args.output_file),
                ],
            )

            # If watch mode is enabled, use the TUI
            if parsed_args.watch:
                return setup_tui_mode(parsed_args)

            return 0
        except Exception as e:
            print_error(f"Error combining files directly: {e}")
            return 1

    except KeyboardInterrupt:
        console.print("\n[bold red]Operation canceled by user.[/bold red]")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.debug("Detailed error:", exc_info=True)
        return 1
