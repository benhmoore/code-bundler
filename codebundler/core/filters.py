"""Filtering operations for file selection."""

import os
from typing import List, Union


def has_matching_extension(filename: str, extensions: Union[str, List[str]]) -> bool:
    """
    Check if a file has any of the specified extensions.

    Args:
        filename: Name of the file to check
        extensions: One or more file extensions to match (must include the dot)

    Returns:
        True if the file has a matching extension, False otherwise
    """
    if not extensions:
        return True  # If no extensions specified, include all files

    # Convert to list if a single string is provided
    if isinstance(extensions, str):
        extensions = [extensions]

    # Get the file extension (with the dot)
    _, file_ext = os.path.splitext(filename)

    # Check if any of the extensions match
    return any(file_ext.lower() == ext.lower() for ext in extensions)


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
