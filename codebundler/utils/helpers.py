"""Helper functions and utilities."""

import argparse
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


def prompt_user(question: str, default: Optional[str] = None) -> str:
    """
    Prompt the user for input with an optional default value.
    
    Args:
        question: Question to ask
        default: Default value if user provides empty input
        
    Returns:
        User's response or default value
    """
    prompt_text = (
        f"{question} [{default}]: " if default is not None else f"{question}: "
    )
    ans = input(prompt_text).strip()
    return ans if ans else (default if default is not None else "")


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
        if not args.source_dir:
            args.source_dir = prompt_user("Enter the source directory to search", ".")
        if not args.output_file:
            args.output_file = prompt_user(
                "Enter path for the combined output file", "combined_output.txt"
            )
        if not args.ext:
            ans = prompt_user("File extension to include (e.g. .py, .js, .cs, .php)", ".py")
            args.ext = ans if ans.startswith(".") else f".{ans}"

        if not args.ignore_names:
            user_in = prompt_user("Ignore filenames containing (comma-separated)?", "")
            if user_in:
                args.ignore_names = [x.strip() for x in user_in.split(",")]

        if not args.ignore_paths:
            user_in = prompt_user("Ignore path segments containing (comma-separated)?", "")
            if user_in:
                args.ignore_paths = [x.strip() for x in user_in.split(",")]

        if not args.include_names:
            user_in = prompt_user(
                "Only include filenames containing (comma-separated)? (Leave blank for all)",
                "",
            )
            if user_in:
                args.include_names = [x.strip() for x in user_in.split(",")]

        if args.strip_comments is None:
            do_strip = prompt_user("Remove single-line comments? (y/n)", "n")
            args.strip_comments = do_strip.lower() in ("y", "yes")

        if args.remove_docstrings is None:
            do_docs = prompt_user("Remove docstrings? (Python only) (y/n)", "n")
            args.remove_docstrings = do_docs.lower() in ("y", "yes")

        # Choose mode if neither export_tree nor use_tree is provided
        if not args.export_tree and not args.use_tree:
            mode = prompt_user(
                "Select mode: (1) Export tree, (2) Use existing tree, (3) Direct combine",
                "3",
            )
            if mode == "1":
                args.export_tree = prompt_user("Path to export tree file", "my_tree.txt")
            elif mode == "2":
                args.use_tree = prompt_user("Path to existing tree file", "my_tree.txt")

        return args