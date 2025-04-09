"""Helper functions and utilities."""

import argparse
import logging
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple, Union

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.theme import Theme

logger = logging.getLogger(__name__)

# Create a custom theme
custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "prompt": "bold cyan",
        "input": "green",
        "panel.border": "cyan",
    }
)

# Create a console with the custom theme
console = Console(theme=custom_theme)


def prompt_user(question: str, default: Optional[str] = None) -> str:
    """
    Prompt the user for input with an optional default value using Rich styling.

    Args:
        question: Question to ask
        default: Default value if user provides empty input

    Returns:
        User's response or default value
    """
    return Prompt.ask(
        f"[prompt]{question}[/prompt]", default=default or "", console=console
    )


def print_info(message: str) -> None:
    """Print an info message with styling."""
    console.print(f"[info]ℹ {message}[/info]")


def print_success(message: str) -> None:
    """Print a success message with styling."""
    console.print(f"[success]✓ {message}[/success]")


def print_warning(message: str) -> None:
    """Print a warning message with styling."""
    console.print(f"[warning]⚠ {message}[/warning]")


def print_error(message: str) -> None:
    """Print an error message with styling."""
    console.print(f"[error]✗ {message}[/error]")


def create_panel(title: str, content: str, style: str = "cyan") -> Panel:
    """Create a Rich panel with the given title and content."""
    return Panel(
        content,
        title=f"[bold {style}]{title}[/bold {style}]",
        border_style=style,
        expand=False,
    )


def display_summary(
    title: str, items: List[Tuple[str, Any]], style: str = "cyan"
) -> None:
    """Display a summary panel with key-value pairs."""
    content = "\n".join([f"[bold]{k}:[/bold] {v}" for k, v in items])
    panel = create_panel(title, content, style)
    console.print(panel)


def prompt_yes_no(question: str, default: bool = False) -> bool:
    """
    Prompt the user for a yes/no answer with styling.

    Args:
        question: Question to ask
        default: Default value if user provides empty input

    Returns:
        Boolean response
    """
    return Confirm.ask(f"[prompt]{question}[/prompt]", default=default, console=console)


@dataclass
class UserOptions:
    """Class to hold user options for the CLI."""

    source_dir: Optional[str] = None
    output_file: Optional[str] = None
    extension: Optional[str] = None
    ignore_names: List[str] = None
    ignore_paths: List[str] = None
    include_names: List[str] = None
    strip_comments: Optional[bool] = None
    remove_docstrings: Optional[bool] = None
    export_tree: Optional[str] = None
    use_tree: Optional[str] = None

    def __post_init__(self):
        """Initialize default values for lists."""
        self.ignore_names = self.ignore_names or []
        self.ignore_paths = self.ignore_paths or []
        self.include_names = self.include_names or []

    def display_summary(self) -> None:
        """Display a summary of the options."""
        items = [
            ("Source Directory", self.source_dir or "Not specified"),
            ("Output File", self.output_file or "Not specified"),
            ("Extension", self.extension or "Not specified"),
            (
                "Ignore Names",
                ", ".join(self.ignore_names) if self.ignore_names else "None",
            ),
            (
                "Ignore Paths",
                ", ".join(self.ignore_paths) if self.ignore_paths else "None",
            ),
            (
                "Include Names",
                ", ".join(self.include_names) if self.include_names else "All",
            ),
            ("Strip Comments", "Yes" if self.strip_comments else "No"),
            ("Remove Docstrings", "Yes" if self.remove_docstrings else "No"),
            ("Export Tree", self.export_tree or "No"),
            ("Use Tree", self.use_tree or "No"),
        ]
        display_summary("Configuration Summary", items)


class InteractiveSetup:
    """Interactive setup for the command line interface."""

    @staticmethod
    def run_interactive(args: argparse.Namespace) -> argparse.Namespace:
        """
        Fill out missing command-line arguments by prompting the user interactively.

        Args:
            args: Parsed command-line arguments

        Returns:
            Updated arguments with missing values filled in
        """
        # Display welcome panel
        console.print(
            Panel(
                "[bold]Welcome to Code Bundler![/bold]\n"
                "This interactive wizard will help you configure the tool.\n"
                "Press Ctrl+C at any time to cancel.",
                title="[bold cyan]Interactive Setup[/bold cyan]",
                border_style="cyan",
                expand=False,
            )
        )

        console.print()
        console.print("[bold cyan]Basic Configuration[/bold cyan]")
        console.print("─" * 50)

        if not args.source_dir:
            args.source_dir = prompt_user("Enter the source directory to search", ".")
        if not args.output_file:
            args.output_file = prompt_user(
                "Enter path for the combined output file", "combined_output.txt"
            )
        if not args.ext:
            ans = prompt_user(
                "File extension to include (e.g. .py, .js, .cs, .php)", ".py"
            )
            args.ext = ans if ans.startswith(".") else f".{ans}"

        console.print()
        console.print("[bold cyan]Filtering Options[/bold cyan]")
        console.print("─" * 50)

        if not args.ignore_names:
            user_in = prompt_user("Ignore filenames containing (comma-separated)?", "")
            if user_in:
                args.ignore_names = [x.strip() for x in user_in.split(",")]

        if not args.ignore_paths:
            user_in = prompt_user(
                "Ignore path segments containing (comma-separated)?", ""
            )
            if user_in:
                args.ignore_paths = [x.strip() for x in user_in.split(",")]

        if not args.include_names:
            user_in = prompt_user(
                "Only include filenames containing (comma-separated)? (Leave blank for all)",
                "",
            )
            if user_in:
                args.include_names = [x.strip() for x in user_in.split(",")]

        console.print()
        console.print("[bold cyan]Transformation Options[/bold cyan]")
        console.print("─" * 50)

        if args.strip_comments is None:
            args.strip_comments = prompt_yes_no("Remove single-line comments?", False)

        if args.remove_docstrings is None:
            args.remove_docstrings = prompt_yes_no(
                "Remove docstrings? (Python only)", False
            )

        console.print()
        console.print("[bold cyan]Operation Mode[/bold cyan]")
        console.print("─" * 50)

        # Choose mode if neither export_tree nor use_tree is provided
        if not args.export_tree and not args.use_tree:
            console.print(
                Panel(
                    "1. [bold]Export Tree:[/bold] Generate a tree file for manual editing\n"
                    "2. [bold]Use Tree:[/bold] Use an existing tree file to combine files\n"
                    "3. [bold]Direct Combine:[/bold] Combine files in one pass",
                    title="[bold cyan]Choose Operation Mode[/bold cyan]",
                    border_style="cyan",
                    expand=False,
                )
            )

            mode = prompt_user("Select mode (1-3)", "3")
            if mode == "1":
                args.export_tree = prompt_user(
                    "Path to export tree file", "my_tree.txt"
                )
            elif mode == "2":
                args.use_tree = prompt_user("Path to existing tree file", "my_tree.txt")

        # Display summary
        console.print()
        options = UserOptions(
            source_dir=args.source_dir,
            output_file=args.output_file,
            extension=args.ext,
            ignore_names=args.ignore_names,
            ignore_paths=args.ignore_paths,
            include_names=args.include_names,
            strip_comments=args.strip_comments,
            remove_docstrings=args.remove_docstrings,
            export_tree=args.export_tree,
            use_tree=args.use_tree,
        )
        options.display_summary()

        # Confirm
        console.print()
        confirm = prompt_yes_no("Proceed with these settings?", True)
        if not confirm:
            console.print("[bold red]Operation canceled by user.[/bold red]")
            import sys

            sys.exit(0)

        return args
