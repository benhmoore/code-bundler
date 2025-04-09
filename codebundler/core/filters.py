"""Filtering operations for file selection."""

from typing import List


def should_include(filename: str, include_names: List[str]) -> bool:
    """
    Decide if a file should be included based on 'include_names'.

    If 'include_names' is empty, include everything.

    Args:
        filename: Name of the file
        include_names: List of keywords to match in filenames

    Returns:
        True if the file should be included, False otherwise
    """
    if not include_names:
        return True
    return any(keyword in filename for keyword in include_names)


def should_ignore(
    filename: str, rel_path: str, ignore_names: List[str], ignore_paths: List[str]
) -> bool:
    """
    Decide if a file or path should be ignored.

    Args:
        filename: Name of the file
        rel_path: Relative path to the file
        ignore_names: List of keywords to ignore in filenames
        ignore_paths: List of keywords to ignore in paths

    Returns:
        True if the file should be ignored, False otherwise
    """
    if any(keyword in filename for keyword in ignore_names):
        return True
    if any(keyword in rel_path for keyword in ignore_paths):
        return True
    return False
