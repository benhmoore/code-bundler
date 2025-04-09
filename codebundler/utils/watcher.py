"""File watching functionality."""

import logging
import time
from pathlib import Path
from typing import Callable, List, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)


class CodeBundlerHandler(FileSystemEventHandler):
    """Event handler for file system changes."""

    def __init__(
        self,
        extension: str,
        ignore_names: List[str],
        ignore_paths: List[str],
        include_names: List[str],
        callback: Callable[[], None],
        output_file: Optional[str] = None,
    ):
        """Initialize the handler with filters and callback."""
        self.extension = extension
        self.ignore_names = ignore_names
        self.ignore_paths = ignore_paths
        self.include_names = include_names
        self.callback = callback
        self.last_run = 0
        self.debounce_time = 0.5  # seconds
        self.output_file = output_file

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Handle file system events."""
        if event.is_directory:
            return

        # Skip non-matching files
        if not event.src_path.endswith(self.extension):
            return

        # Prevent infinite loops by ignoring the output file
        if (
            self.output_file
            and Path(event.src_path).resolve() == Path(self.output_file).resolve()
        ):
            logger.debug(f"Ignoring changes to output file: {event.src_path}")
            return

        # Apply filtering logic
        from codebundler.core.filters import should_ignore, should_include

        rel_path = Path(event.src_path).name
        if should_ignore(
            rel_path, event.src_path, self.ignore_names, self.ignore_paths
        ):
            return
        if not should_include(rel_path, self.include_names):
            return

        # Debounce to prevent multiple rapid rebuilds
        current_time = time.time()
        if current_time - self.last_run < self.debounce_time:
            return

        self.last_run = current_time
        logger.info(f"File changed: {event.src_path}")
        self.callback()


def watch_directory(
    source_dir: str,
    extension: str,
    ignore_names: List[str],
    ignore_paths: List[str],
    include_names: List[str],
    callback: Callable[[], None],
    output_file: Optional[str] = None,
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
        output_file: Path to output file to ignore (prevents infinite loops)

    Returns:
        The observer object (call observer.stop() to stop watching)
    """
    event_handler = CodeBundlerHandler(
        extension=extension,
        ignore_names=ignore_names,
        ignore_paths=ignore_paths,
        include_names=include_names,
        callback=callback,
        output_file=output_file,
    )

    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=True)
    observer.start()
    return observer
