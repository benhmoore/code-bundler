"""Command line interface for the package."""

import argparse
import logging
import os
import sys
import time
from typing import List, Optional

from rich.table import Table

from codebundler import __version__

# Import utility functions
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
    basic_group = parser.add_argument_group("Basic Options")
    tui_group = parser.add_argument_group("TUI Options")
    transform_group = parser.add_argument_group("Transformation Options")

    # Information options
    info_group.add_argument(
        "--version",
        action="version",
        version=f"codebundler {__version__}",
        help="Show version information and exit.",
    )

    # Configure TUI specific options

    tui_group.add_argument(
        "--ignore",
        dest="hide_patterns",
        type=str,
        nargs="?",
        const="__pycache__,*.meta",  # Default if flag is provided without argument
        default="",  # Default if flag is not provided
        metavar="PATTERNS",
        help="Comma-separated patterns to ignore in tree view (e.g., --ignore='__pycache__,*.meta')",
    )

    tui_group.add_argument(
        "--select",
        dest="select_patterns",
        type=str,
        nargs="?",
        const="*.py",  # Default if flag is provided without argument
        default="",  # Default if flag is not provided
        metavar="PATTERNS",
        help="Comma-separated glob patterns (must be quoted) for file selection (e.g., --select='*.py,*.md')",
    )

    tui_group.add_argument(
        "-y",
        "--yes",
        action="store_false",
        dest="confirm_selection",
        help="Auto-confirm directory tree and begin watching immediately",
    )

    # Required arguments
    basic_group.add_argument(
        "source_dir", metavar="DIRECTORY", help="Directory to search/watch (required)"
    )

    basic_group.add_argument(
        "output_file", metavar="OUTPUT", help="Output file path (required)"
    )

    # Legacy filtering options - moved to TUI selection

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

    # Basic verbosity options
    basic_group.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )

    basic_group.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress non-error output."
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
        # Source dir and output file are now required positional arguments

        # Import the TUI app
        try:
            from codebundler.tui.app import CodeBundlerApp
        except ImportError as e:
            print_error(
                f"Error importing TUI modules: {e}\n"
                "Make sure all dependencies are installed: pip install -e ."
            )
            return 1

        print_info("Launching TUI mode...")

        # Start the TUI application
        app = CodeBundlerApp(
            watch_path=parsed_args.source_dir,
            output_file=parsed_args.output_file,
            # Extension will be auto-detected from the output file
            hide_patterns=parsed_args.hide_patterns,
            select_patterns=parsed_args.select_patterns,
            ignore_names=None,
            ignore_paths=None,
            include_names=None,
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

        # Launch TUI interface
        # Parse comma-separated patterns into lists
        if parsed_args.select_patterns and isinstance(parsed_args.select_patterns, str):
            parsed_args.select_patterns = [
                p.strip() for p in parsed_args.select_patterns.split(",") if p.strip()
            ]

        if parsed_args.hide_patterns and isinstance(parsed_args.hide_patterns, str):
            parsed_args.hide_patterns = [
                p.strip() for p in parsed_args.hide_patterns.split(",") if p.strip()
            ]

        return setup_tui_mode(parsed_args)

    except KeyboardInterrupt:
        console.print("\n[bold red]Operation canceled by user.[/bold red]")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        logger.debug("Detailed error:", exc_info=True)
        return 1
