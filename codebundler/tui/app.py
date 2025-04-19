"""Main TUI application for CodeBundler."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Set

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Grid, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, Static, Tree

from codebundler.tui.bundler import create_bundle
from codebundler.tui.widgets.directory_tree import DirectoryTree
from codebundler.utils.watcher import watch_directory

logger = logging.getLogger(__name__)


class HelpScreen(ModalScreen):
    """Help screen modal that displays all available keyboard shortcuts."""

    CSS = """
    #help-container {
        width: 60%;
        height: 70%;
        background: $surface;
        border: solid $primary;
        padding: 1 2;
    }
    
    #help-title {
        text-align: center;
        background: $boost;
        padding: 1;
        width: 100%;
        color: $text;
        text-style: bold;
        margin-bottom: 1;
    }
    
    .shortcut-grid {
        height: auto;
        margin-top: 1;
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: auto;
    }
    
    .key {
        background: $boost;
        color: $text-muted;
        padding: 0 1;
        text-align: center;
        border: solid $primary-darken-3;
    }
    
    .description {
        padding-left: 1;
        color: $text;
    }
    
    #close-button-row {
        align: center middle;
        height: auto;
        margin-top: 2;
    }
    
    #close-button {
        width: 30%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the help screen content."""
        with Container(id="help-container"):
            yield Label("CodeBundler Keyboard Shortcuts", id="help-title")

            with Grid(classes="shortcut-grid"):
                # Define shortcut rows with key and description
                shortcuts = [
                    ("Enter", "Toggle selection of current node"),
                    ("Space", "Toggle selection of current node"),
                    ("a", "Select all files"),
                    ("n", "Deselect all files"),
                    ("r", "Rebuild the bundle"),
                    ("c", "Copy bundle to clipboard"),
                    ("h", "Show/hide this help screen"),
                    ("q", "Quit the application"),
                ]

                # Add CSS grid classes
                yield Static("Key", classes="key")
                yield Static("Description", classes="description")

                # Add all shortcuts to the grid
                for key, description in shortcuts:
                    yield Static(key, classes="key")
                    yield Static(description, classes="description")

            with Horizontal(id="close-button-row"):
                yield Button("Close (Esc)", id="close-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "close-button":
            self.dismiss()

    def on_key(self, event) -> None:
        """Handle key press events."""
        if event.key == "escape":
            self.dismiss()


class StatusBar(Static):
    """Status bar widget to display current status and messages."""

    def __init__(self) -> None:
        """Initialize the status bar with default message."""
        super().__init__("Ready - Press 'h' for help")
        self.status = "Ready - Press 'h' for help"

    def update_status(self, message: str, style: str = "white") -> None:
        """Update the status message with optional styling."""
        self.status = message
        self.update(Text(message, style=style))


class CodeBundlerApp(App):
    """Main TUI application for CodeBundler."""

    CSS = """
    #main-container {
        width: 100%;
        height: 100%;
    }
    
    #sidebar {
        width: 50%;  /* Make wider to show more of the file tree */
        min-width: 30;
        border-right: solid $primary;
    }
    
    #file-tree {
        height: 100%;
        overflow: auto;
        background: $surface-darken-1;  /* Better contrast for tree */
    }
    
    Tree:focus > .tree--cursor {
        background: $accent;  /* Highlight selected item in tree */
        color: $text;
    }
    
    #main-content {
        width: 50%;
        padding: 1;
    }
    
    #status-bar {
        height: 1;
        dock: bottom;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    
    .title {
        background: $boost;
        color: $text;
        padding: 1 2;
        text-align: center;
        text-style: bold;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "rebuild", "Rebuild"),
        ("a", "select_all", "Select All"),
        ("n", "deselect_all", "Deselect All"),
        ("c", "copy_to_clipboard", "Copy to Clipboard"),
        ("h", "toggle_help", "Show/Hide Help"),
        ("enter", "toggle_selection", "Toggle Selection"),
        ("space", "toggle_selection", "Toggle Selection"),
    ]

    # Define class variables to hold widget references
    tree: DirectoryTree = None
    bundle_status: Label = None
    status_bar: "StatusBar" = None

    def __init__(
        self,
        watch_path: str,
        output_file: str,
        extension: str = None,
        hide_patterns: List[str] = None,
        select_patterns: List[str] = None,
        ignore_names: List[str] = None,
        ignore_paths: List[str] = None,
        include_names: List[str] = None,
        strip_comments: bool = False,
        remove_docstrings: bool = False,
        confirm_selection: bool = True,
    ):
        """Initialize the application with configuration parameters."""
        super().__init__()
        self.watch_path = Path(watch_path).resolve()
        self.output_file = output_file

        # We don't filter by extension in the TUI
        self.extension = None
        self.hide_patterns = hide_patterns or []
        self.select_patterns = select_patterns or []
        self.ignore_names = ignore_names or []
        self.ignore_paths = ignore_paths or []
        self.include_names = include_names or []
        self.strip_comments = strip_comments
        self.remove_docstrings = remove_docstrings
        self.confirm_selection = confirm_selection
        self.selected_files = set()
        self.observer = None

    def compose(self) -> ComposeResult:
        """Compose the user interface layout."""
        with Container(id="main-container"):
            yield Header()
            with Horizontal():
                with Vertical(id="sidebar"):
                    yield Label("File Selection (click to select)", classes="title")
                    yield DirectoryTree(
                        self.watch_path,
                        id="file-tree",
                        extension=self.extension,
                        hide_patterns=self.hide_patterns,
                        select_patterns=self.select_patterns,
                    )

                with Vertical(id="main-content"):
                    yield Label("Output Configuration", classes="title")
                    # We'll add transform options and output status here
                    yield Label(f"Output File: {self.output_file}")
                    yield Label(
                        f"Strip Comments: {'Yes' if self.strip_comments else 'No'}"
                    )
                    yield Label(
                        f"Remove Docstrings: {'Yes' if self.remove_docstrings else 'No'}"
                    )

                    # Bundle status and information
                    self.bundle_status = Label("No bundle generated yet")
                    yield self.bundle_status

            self.status_bar = StatusBar()
            yield self.status_bar
            yield Footer()

    async def on_mount(self) -> None:
        """Set up the application when it first mounts."""
        # Get the directory tree widget
        self.tree = self.query_one(DirectoryTree)

        # Set up initial selection based on patterns
        await self.tree.setup_initial_selection(self.select_patterns)

        # Set up file watcher
        self.setup_file_watcher()

        # Build initial bundle if no confirmation needed
        if not self.confirm_selection:
            self.rebuild_bundle()

    def setup_file_watcher(self) -> None:
        """Set up the file watcher to monitor changes in the watch path."""
        try:
            self.status_bar.update_status("Setting up file watcher...", "yellow")
            self.observer = watch_directory(
                source_dir=str(self.watch_path),
                extension=self.extension,
                ignore_names=self.ignore_names,
                ignore_paths=self.ignore_paths,
                include_names=self.include_names,
                callback=lambda changed_file: self.call_later(
                    self.on_file_changed, changed_file
                ),
            )
            self.status_bar.update_status(
                f"Watching {self.watch_path} for changes", "green"
            )
        except Exception as e:
            self.status_bar.update_status(f"Error setting up watcher: {e}", "red")
            logger.error(f"Error setting up file watcher: {e}")

    def on_file_changed(self, changed_file: str) -> None:
        """Handle file system change events."""
        self.status_bar.update_status(f"File changed: {changed_file}", "yellow")

        # Update the tree to reflect file system changes
        self.tree.refresh_tree()

        # Rebuild the bundle if the changed file is selected
        file_path = str(Path(changed_file).resolve())
        if file_path in self.selected_files:
            self.rebuild_bundle()

    def on_tree_node_highlighted(self, node):
        """Update status based on current node highlight."""
        if hasattr(node, "data") and node.data:
            path = node.data.get("path", "")
            if node.data.get("is_dir", False):
                self.status_bar.update_status(f"Directory: {path}")
            else:
                if node.data.get("selected", False):
                    self.status_bar.update_status(f"Selected: {path}", "green")
                else:
                    self.status_bar.update_status(f"Click to select: {path}", "cyan")

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection events from the directory tree."""
        self.selected_files = event.selected_files
        self.status_bar.update_status(
            f"{len(self.selected_files)} files selected", "cyan"
        )

    @on(Tree.NodeHighlighted)
    def on_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Handle node highlight events from the tree."""
        self.on_tree_node_highlighted(event.node)

    @work
    async def rebuild_bundle(self) -> None:
        """Rebuild the bundle file based on current selection."""
        if not self.selected_files:
            self.status_bar.update_status("No files selected for bundling", "yellow")
            return

        self.status_bar.update_status(
            f"Bundling {len(self.selected_files)} files...", "yellow"
        )

        try:
            # Convert absolute paths back to relative for the combiner
            relative_paths = [
                os.path.relpath(file_path, str(self.watch_path))
                for file_path in self.selected_files
            ]

            # Create the bundle with our clean implementation
            processed_count = create_bundle(
                source_dir=str(self.watch_path),
                output_file=self.output_file,
                file_paths=list(self.selected_files),  # Use absolute paths
                extension=self.extension,
                remove_comments=self.strip_comments,
                remove_docstrings=self.remove_docstrings,
            )

            # Update status
            self.status_bar.update_status(
                f"Bundle updated: {processed_count} files written to {self.output_file}",
                "green",
            )

            # Get file stats
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    total_lines = content.count("\n") + 1
                    total_size = len(content)

                self.bundle_status.update(
                    f"Bundle: {processed_count} files, {total_lines} lines, {total_size/1024:.1f} KB"
                )
            except Exception as e:
                logger.error(f"Error reading output file stats: {e}")

        except Exception as e:
            self.status_bar.update_status(f"Error creating bundle: {e}", "red")
            logger.error(f"Error creating bundle: {e}")

    def action_rebuild(self) -> None:
        """Rebuild the bundle (triggered by key binding)."""
        self.rebuild_bundle()

    def action_select_all(self) -> None:
        """Select all matching files in the tree."""
        self.tree.select_all_matching_files()

    def action_deselect_all(self) -> None:
        """Deselect all files in the tree."""
        self.tree.deselect_all_files()

    def action_toggle_selection(self) -> None:
        """Toggle selection of the currently highlighted node (triggered by Space or Enter keys)."""
        if self.tree._highlighted_node:
            self.tree.toggle_selection(self.tree._highlighted_node)

    def action_copy_to_clipboard(self) -> None:
        """Copy the bundled content to the clipboard."""
        try:
            if not os.path.exists(self.output_file):
                self.status_bar.update_status(
                    "No bundle file found. Build first with 'r'", "yellow"
                )
                return

            # First rebuild to ensure we have the latest content
            self.rebuild_bundle()

            # Read the file content
            with open(self.output_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Copy to clipboard using pyperclip or OS command
            try:
                import pyperclip

                pyperclip.copy(content)
                self.status_bar.update_status(
                    f"Copied {len(content)} characters to clipboard", "green"
                )
            except ImportError:
                # Fall back to OS-specific commands if pyperclip is not available
                import platform
                import subprocess

                system = platform.system()
                if system == "Darwin":  # macOS
                    process = subprocess.Popen(
                        ["pbcopy"], stdin=subprocess.PIPE, text=True
                    )
                    process.communicate(input=content)
                    self.status_bar.update_status(
                        f"Copied {len(content)} characters to clipboard", "green"
                    )
                elif system == "Windows":
                    process = subprocess.Popen(
                        ["clip"], stdin=subprocess.PIPE, text=True
                    )
                    process.communicate(input=content)
                    self.status_bar.update_status(
                        f"Copied {len(content)} characters to clipboard", "green"
                    )
                elif system == "Linux":
                    try:
                        # Try xclip first
                        process = subprocess.Popen(
                            ["xclip", "-selection", "clipboard"],
                            stdin=subprocess.PIPE,
                            text=True,
                        )
                        process.communicate(input=content)
                        self.status_bar.update_status(
                            f"Copied {len(content)} characters to clipboard", "green"
                        )
                    except FileNotFoundError:
                        try:
                            # Try xsel if xclip is not available
                            process = subprocess.Popen(
                                ["xsel", "--clipboard", "--input"],
                                stdin=subprocess.PIPE,
                                text=True,
                            )
                            process.communicate(input=content)
                            self.status_bar.update_status(
                                f"Copied {len(content)} characters to clipboard",
                                "green",
                            )
                        except FileNotFoundError:
                            self.status_bar.update_status(
                                "Clipboard copy failed. Install pyperclip, xclip, or xsel.",
                                "red",
                            )
                else:
                    self.status_bar.update_status(
                        f"Clipboard not supported on {system}", "red"
                    )

        except Exception as e:
            self.status_bar.update_status(f"Error copying to clipboard: {e}", "red")
            logger.error(f"Error copying to clipboard: {e}")

    def action_toggle_help(self) -> None:
        """Toggle the help screen."""
        self.push_screen(HelpScreen())

    def on_unmount(self) -> None:
        """Clean up when the application exits."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
