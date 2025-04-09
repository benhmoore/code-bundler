"""Command line interface for the package."""

import argparse
import logging
import os
import sys
import time
from typing import Dict, List, Optional

from rich.table import Table

from codebundler import __version__
from codebundler.core.combiner import combine_from_filelist, combine_source_files
from codebundler.core.tree import generate_tree_file, parse_tree_file
from codebundler.utils.helpers import (
    InteractiveSetup,
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

    # Operation modes
    mode_group.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in guided, interactive mode.",
    )

    mode_group.add_argument(
        "--export-tree",
        metavar="FILE",
        help="Path to export a proposed tree (for manual editing).",
    )

    mode_group.add_argument(
        "--use-tree", metavar="FILE", help="Path to an edited tree file to combine."
    )

    # Basic options (possibly missing in interactive mode)
    basic_group.add_argument(
        "source_dir", nargs="?", default=None, help="Directory to search."
    )

    basic_group.add_argument(
        "output_file", nargs="?", default=None, help="Output file path."
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
        help="Watch for file changes and rebuild automatically.",
    )

    # We want None as default so we can detect if user explicitly set these flags
    parser.set_defaults(strip_comments=None, remove_docstrings=None)

    return parser


def display_welcome_banner() -> None:
    """Display a welcome banner when the application starts."""
    title = "[bold cyan]Code Bundler[/bold cyan]"
    version_str = f"[dim]v{__version__}[/dim]"

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

        # ----------------------------------------------------
        # Handle exclusive flags first
        # ----------------------------------------------------
        if parsed_args.export_tree and parsed_args.use_tree:
            print_error("Cannot use --export-tree and --use-tree at the same time.")
            return 1

        # ----------------------------------------------------
        # If we're using a tree, parse it NOW (before interactive)
        # ----------------------------------------------------
        filelist = []
        if parsed_args.use_tree:
            print_info(f"Parsing tree file: {parsed_args.use_tree}")

            with console.status(
                f"[cyan]Reading tree file {parsed_args.use_tree}...[/cyan]"
            ):
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

            if (
                parsed_args.remove_docstrings is None
                and tree_remove_docstrings is not None
            ):
                parsed_args.remove_docstrings = tree_remove_docstrings
                logger.debug(
                    f"Using remove_docstrings setting from tree: {tree_remove_docstrings}"
                )

            # Display info from tree
            if filelist:
                display_summary(
                    "Tree File Info",
                    [
                        ("Source Directory", tree_source_dir or "Not specified"),
                        ("Output File", tree_output_file or "Not specified"),
                        ("Extension", tree_extension or "Not specified"),
                        ("Strip Comments", "Yes" if tree_strip_comments else "No"),
                        (
                            "Remove Docstrings",
                            "Yes" if tree_remove_docstrings else "No",
                        ),
                        ("Files Found", len(filelist)),
                    ],
                )

        # ----------------------------------------------------
        # Possibly go interactive now (only if requested or no data)
        # ----------------------------------------------------
        # If user did not explicitly set --use-tree, or if we still
        # have missing arguments AND user asked for interactive mode, prompt them.
        # (If the user used --use-tree without --interactive and the tree file
        #  has all the data, we won't prompt.)
        needs_essential_args = (
            not parsed_args.source_dir
            or not parsed_args.output_file
            or not parsed_args.ext
        )
        if parsed_args.interactive or (needs_essential_args and sys.stdin.isatty()):
            print_info("Running in interactive mode")
            parsed_args = InteractiveSetup.run_interactive(parsed_args)

        # ----------------------------------------------------
        # 1) Export tree
        # ----------------------------------------------------
        if parsed_args.export_tree:
            console.print(
                create_panel(
                    "Export Tree Mode",
                    f"[bold]Source:[/bold] {parsed_args.source_dir}\n"
                    f"[bold]Tree File:[/bold] {parsed_args.export_tree}\n"
                    f"[bold]Extension:[/bold] {parsed_args.ext}",
                    "green",
                )
            )

            try:
                with console.status(
                    f"[cyan]Scanning directory {parsed_args.source_dir}...[/cyan]"
                ):
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

                print_success(
                    f"Exported tree with {file_count} matching files to {parsed_args.export_tree}."
                )

                # Display next steps
                console.print(
                    create_panel(
                        "Next Steps",
                        f"1. Edit the tree file: {parsed_args.export_tree}\n"
                        f"2. Remove any lines for files you don't want to include\n"
                        f"3. Run again with: codebundler --use-tree {parsed_args.export_tree}",
                        "cyan",
                    )
                )

                return 0
            except Exception as e:
                print_error(f"Error exporting tree: {e}")
                return 1

        # ----------------------------------------------------
        # 2) Use tree (already parsed)
        # ----------------------------------------------------
        if parsed_args.use_tree:
            # Check for missing info
            if not parsed_args.source_dir:
                print_error(
                    "No source directory provided (and none found in the tree)."
                )
                return 1
            if not parsed_args.output_file:
                print_error("No output file provided (and none found in the tree).")
                return 1
            if not parsed_args.ext:
                print_error("No extension provided (and none found in the tree).")
                return 1
            if not filelist:
                print_warning("No valid file paths found in the tree file.")
                return 0

            console.print(
                create_panel(
                    "Tree Mode",
                    f"[bold]Source:[/bold] {parsed_args.source_dir}\n"
                    f"[bold]Output:[/bold] {parsed_args.output_file}\n"
                    f"[bold]Tree File:[/bold] {parsed_args.use_tree}\n"
                    f"[bold]Files to Process:[/bold] {len(filelist)}",
                    "green",
                )
            )

            try:
                # Simple status message instead of progress bar
                with console.status(f"[cyan]Combining {len(filelist)} files...[/cyan]"):
                    processed_count = combine_from_filelist(
                        source_dir=parsed_args.source_dir,
                        output_file=parsed_args.output_file,
                        extension=parsed_args.ext,
                        filelist=filelist,
                        remove_comments=bool(parsed_args.strip_comments),
                        remove_docstrings=bool(parsed_args.remove_docstrings),
                    )

                print_success(
                    f"Combined {processed_count} files into '{parsed_args.output_file}' from tree '{parsed_args.use_tree}'."
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

                # If watch mode is enabled, set up the watcher
                if parsed_args.watch:
                    return setup_watch_mode(
                        parsed_args, filelist=filelist, use_tree=True
                    )

                return 0
            except Exception as e:
                print_error(f"Error combining files from tree: {e}")
                return 1

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

            # If watch mode is enabled, set up the watcher
            if parsed_args.watch:
                return setup_watch_mode(parsed_args, filelist=None, use_tree=False)

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


def setup_watch_mode(parsed_args, filelist=None, use_tree=False):
    """
    Set up file watching for automatic rebuilding.

    Args:
        parsed_args: Command line arguments
        filelist: List of files to watch (if using tree mode)
        use_tree: Whether we're using a tree file

    Returns:
        Exit code
    """
    try:
        # Import here to avoid dependency for users who don't need watch
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler, FileSystemEvent
        except ImportError:
            print_error(
                "Watching requires the 'watchdog' package. "
                "Install with: pip install codebundler[watch] or pip install watchdog"
            )
            return 1

        print_info("Watching for file changes. Press Ctrl+C to stop.")
        console.print(
            create_panel(
                "Watch Mode",
                f"[bold]Source Directory:[/bold] {parsed_args.source_dir}\n"
                f"[bold]Output File:[/bold] {parsed_args.output_file}\n"
                f"[bold]Press Ctrl+C to stop watching[/bold]",
                "cyan",
            )
        )

        class CodeBundlerHandler(FileSystemEventHandler):
            """Event handler for file system changes."""

            def __init__(
                self,
                extension: str,
                ignore_names: List[str],
                ignore_paths: List[str],
                include_names: List[str],
                callback,
            ):
                """Initialize the handler with filters and callback."""
                self.extension = extension
                self.ignore_names = ignore_names
                self.ignore_paths = ignore_paths
                self.include_names = include_names
                self.callback = callback
                self.last_run = 0
                self.debounce_time = 0.5  # seconds

            def on_any_event(self, event: FileSystemEvent) -> None:
                """Handle file system events."""
                if event.is_directory:
                    return

                # Skip non-matching files
                if not event.src_path.endswith(self.extension):
                    return

                # Apply filtering logic
                from codebundler.core.filters import should_ignore, should_include

                filename = os.path.basename(event.src_path)
                rel_path = os.path.relpath(event.src_path, parsed_args.source_dir)
                rel_path = rel_path.replace("\\", "/")

                if should_ignore(
                    filename, rel_path, self.ignore_names, self.ignore_paths
                ):
                    return
                if not should_include(filename, self.include_names):
                    return

                # For tree mode, check if the file is in our list
                if use_tree and filelist and rel_path not in filelist:
                    return

                # Debounce to prevent multiple rapid rebuilds
                current_time = time.time()
                if current_time - self.last_run < self.debounce_time:
                    return

                self.last_run = current_time
                logger.info(f"File changed: {rel_path}")
                self.callback(rel_path)

        # Define a callback function for rebuilding
        def rebuild(changed_file=None):
            console.print(f"[cyan]Rebuilding... (triggered by {changed_file})[/cyan]")
            try:
                if use_tree:
                    combine_from_filelist(
                        source_dir=parsed_args.source_dir,
                        output_file=parsed_args.output_file,
                        extension=parsed_args.ext,
                        filelist=filelist,
                        remove_comments=bool(parsed_args.strip_comments),
                        remove_docstrings=bool(parsed_args.remove_docstrings),
                    )
                else:
                    combine_source_files(
                        source_dir=parsed_args.source_dir,
                        output_file=parsed_args.output_file,
                        extension=parsed_args.ext,
                        ignore_names=parsed_args.ignore_names,
                        ignore_paths=parsed_args.ignore_paths,
                        include_names=parsed_args.include_names,
                        remove_comments=bool(parsed_args.strip_comments),
                        remove_docstrings=bool(parsed_args.remove_docstrings),
                    )
                console.print(
                    f"[green]Rebuild complete: {parsed_args.output_file}[/green]"
                )
            except Exception as e:
                print_error(f"Error during rebuild: {e}")

        # Set up the event handler
        event_handler = CodeBundlerHandler(
            extension=parsed_args.ext,
            ignore_names=parsed_args.ignore_names,
            ignore_paths=parsed_args.ignore_paths,
            include_names=parsed_args.include_names,
            callback=rebuild,
        )

        # Set up the observer
        observer = Observer()
        observer.schedule(event_handler, parsed_args.source_dir, recursive=True)
        observer.start()

        try:
            # Keep the main thread running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[cyan]Stopping watch mode...[/cyan]")
            observer.stop()
        observer.join()

        return 0

    except Exception as e:
        print_error(f"Error setting up watch mode: {e}")
        return 1
