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


# Utility functions for CLI and TUI interfaces
