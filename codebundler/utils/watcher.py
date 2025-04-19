"""File watching functionality."""

import logging
import os
import time
from pathlib import Path
from typing import Callable, List

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from codebundler.core.filters import should_ignore, should_include

logger = logging.getLogger(__name__)


class CodeBundlerHandler(FileSystemEventHandler):
    """Event handler for file system changes."""

    def __init__(
        self,
        source_dir: str,
        extension: str,
        ignore_names: List[str] = None,
        ignore_paths: List[str] = None,
        include_names: List[str] = None,
        callback: Callable[[str], None] = None,
    ):
        """Initialize the handler with filters and callback."""
        self.source_dir = source_dir
        self.extension = extension
        self.ignore_names = ignore_names or []
        self.ignore_paths = ignore_paths or []
        self.include_names = include_names or []
        # No tree-based selection parameters needed
        self.callback = callback
        self.last_run = 0
        self.debounce_time = 0.5  # seconds
        self.last_changed_file = None

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle file system events."""
        if event.is_directory:
            return

        # Skip non-matching files
        if not event.src_path.endswith(self.extension):
            return

        # Apply filtering logic
        filename = os.path.basename(event.src_path)
        rel_path = os.path.relpath(event.src_path, self.source_dir)
        rel_path = rel_path.replace("\\", "/")

        if should_ignore(filename, rel_path, self.ignore_names, self.ignore_paths):
            return
        if not should_include(filename, self.include_names):
            return

        # Apply TUI-specific selection logic

        # Debounce to prevent multiple rapid rebuilds
        current_time = time.time()
        if current_time - self.last_run < self.debounce_time:
            return

        # Store the changed file path and trigger callback
        self.last_changed_file = rel_path
        self.last_run = current_time
        logger.info(f"File changed: {self.last_changed_file}")

        if self.callback:
            self.callback(self.last_changed_file)


def watch_directory(
    source_dir: str,
    extension: str,
    ignore_names: List[str] = None,
    ignore_paths: List[str] = None,
    include_names: List[str] = None,
    callback: Callable[[str], None] = None,
) -> Observer:
    """
    Watch a directory for changes and trigger the callback when files change.

    Args:
        source_dir: Directory to watch
        extension: File extension to monitor
        ignore_names: List of filename patterns to ignore
        ignore_paths: List of path patterns to ignore
        include_names: List of filename patterns to include
        callback: Function to call when changes are detected

    Returns:
        The observer object (call observer.stop() to stop watching)
    """
    event_handler = CodeBundlerHandler(
        source_dir=source_dir,
        extension=extension,
        ignore_names=ignore_names,
        ignore_paths=ignore_paths,
        include_names=include_names,
        callback=callback,
    )

    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=True)
    observer.start()
    return observer
