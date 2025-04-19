"""Main TUI application for CodeBundler."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Set

from rich.text import Text
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Label, Static

from codebundler.tui.bundler import create_bundle
from codebundler.tui.widgets.directory_tree import DirectoryTree
from codebundler.utils.watcher import watch_directory

logger = logging.getLogger(__name__)


class StatusBar(Static):
    """Status bar widget to display current status and messages."""

    def __init__(self) -> None:
        """Initialize the status bar with default message."""
        super().__init__("Ready")
        self.status = "Ready"

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
        width: 30%;
        min-width: 20;
        border-right: solid $primary;
    }
    
    #file-tree {
        height: 100%;
        overflow: auto;
    }
    
    #main-content {
        width: 70%;
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
    ]

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
        
        # Auto-detect extension from output file if not provided
        if extension is None:
            output_ext = Path(output_file).suffix
            self.extension = output_ext if output_ext else '.py'  # Default to .py if no extension
        else:
            self.extension = extension if extension.startswith('.') else f'.{extension}'
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
                    yield Label("File Selection", classes="title")
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
                    yield Label(f"Strip Comments: {'Yes' if self.strip_comments else 'No'}")
                    yield Label(f"Remove Docstrings: {'Yes' if self.remove_docstrings else 'No'}")
                    
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
                callback=lambda changed_file: self.call_later(self.on_file_changed, changed_file),
            )
            self.status_bar.update_status(f"Watching {self.watch_path} for changes", "green")
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

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection events from the directory tree."""
        self.selected_files = event.selected_files
        self.status_bar.update_status(f"{len(self.selected_files)} files selected", "cyan")

    @work
    async def rebuild_bundle(self) -> None:
        """Rebuild the bundle file based on current selection."""
        if not self.selected_files:
            self.status_bar.update_status("No files selected for bundling", "yellow")
            return

        self.status_bar.update_status(f"Bundling {len(self.selected_files)} files...", "yellow")
        
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
                "green"
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

    def on_unmount(self) -> None:
        """Clean up when the application exits."""
        if self.observer:
            self.observer.stop()
            self.observer.join()