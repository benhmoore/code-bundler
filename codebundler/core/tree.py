"""Tree file generation and parsing operations."""

import logging
import os
from typing import List, Optional, Tuple

from codebundler.core.filters import should_ignore, should_include

logger = logging.getLogger(__name__)


def generate_tree_file(
    source_dir: str,
    tree_output_path: str,
    extension: str,
    ignore_names: List[str],
    ignore_paths: List[str],
    include_names: List[str],
    output_file: Optional[str] = None,
    remove_comments: bool = False,
    remove_docstrings: bool = False,
) -> int:
    """
    Create a 'tree' file listing directories and matching files.

    Writes relevant user selections at the top of the file:
      - Source directory
      - Output file
      - Whether to strip comments
      - Whether to remove docstrings
    Then a proposed inclusion list for the extension.

    Args:
        source_dir: Directory to search for files
        tree_output_path: Path to write the tree file
        extension: File extension to match
        ignore_names: List of keywords to ignore in filenames
        ignore_paths: List of keywords to ignore in paths
        include_names: List of keywords to match in filenames
        output_file: Target output file path (optional)
        remove_comments: Whether to remove comments
        remove_docstrings: Whether to remove docstrings

    Returns:
        Number of matching files found
    """
    lines = []
    file_count = 0

    def walk_tree(current_path: str, prefix: str = "") -> None:
        nonlocal file_count

        try:
            entries = sorted(os.listdir(current_path))
        except (PermissionError, FileNotFoundError) as e:
            logger.warning(f"Could not read directory {current_path}: {e}")
            return

        for i, entry in enumerate(entries):
            full_path = os.path.join(current_path, entry)
            rel_path = os.path.relpath(full_path, source_dir).replace("\\", "/")
            connector = "└── " if i == len(entries) - 1 else "├── "
            is_file = os.path.isfile(full_path)

            if is_file:
                if (
                    entry.endswith(extension)
                    and not should_ignore(entry, rel_path, ignore_names, ignore_paths)
                    and should_include(entry, include_names)
                ):
                    lines.append(f"{prefix}{connector}{rel_path}")
                    file_count += 1
            else:
                # Also list directories (so user sees structure)
                if not should_ignore(entry, rel_path, ignore_names, ignore_paths):
                    lines.append(f"{prefix}{connector}{rel_path}")
                    new_prefix = "    " if i == len(entries) - 1 else "│   "
                    walk_tree(full_path, prefix + new_prefix)

    walk_tree(source_dir)

    with open(tree_output_path, "w", encoding="utf-8") as f:
        f.write(f"# Source Directory: {source_dir}\n")
        if output_file:
            f.write(f"# Output File: {output_file}\n")
        f.write(f"# Extension: {extension}\n")
        f.write(f"# Strip Comments: {'yes' if remove_comments else 'no'}\n")
        f.write(f"# Remove Docstrings: {'yes' if remove_docstrings else 'no'}\n")
        f.write(f"# Proposed inclusion list for files ending in '{extension}'\n")
        f.write("# Delete or comment out any lines for files you want to exclude.\n")
        f.write(
            "# Lines for directories are ignored when combining (only files matter).\n\n"
        )
        f.write("\n".join(lines))

    return file_count


def parse_tree_file(
    tree_file_path: str,
) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[bool],
    Optional[bool],
    List[str],
]:
    """
    Parse a tree file created by generate_tree_file.

    Args:
        tree_file_path: Path to the tree file

    Returns:
        Tuple containing:
          - source_dir_in_file: Source directory found in tree file
          - output_file_in_file: Output file found in tree file
          - extension_in_file: File extension found in tree file
          - remove_comments_in_file: Whether to remove comments
          - remove_docstrings_in_file: Whether to remove docstrings
          - included_paths: List of paths to include
    """
    source_dir_in_file = None
    output_file_in_file = None
    extension_in_file = None
    remove_comments_in_file = None
    remove_docstrings_in_file = None
    included_paths: List[str] = []

    try:
        with open(tree_file_path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    # Header lines
                    lower = stripped.lower()
                    if lower.startswith("# source directory:"):
                        source_dir_in_file = stripped.split(":", 1)[1].strip()
                    elif lower.startswith("# output file:"):
                        output_file_in_file = stripped.split(":", 1)[1].strip()
                    elif lower.startswith("# extension:"):
                        extension_in_file = stripped.split(":", 1)[1].strip()
                    elif lower.startswith("# strip comments:"):
                        val = stripped.split(":", 1)[1].strip().lower()
                        remove_comments_in_file = val == "yes"
                    elif lower.startswith("# remove docstrings:"):
                        val = stripped.split(":", 1)[1].strip().lower()
                        remove_docstrings_in_file = val == "yes"
                    # Ignore other comment lines
                    continue

                # Non-comment lines with "──" are included files/dirs
                if "──" in stripped:
                    path_part = stripped.split("──", 1)[-1].strip()
                    included_paths.append(path_part)
    except (IOError, UnicodeDecodeError) as e:
        logger.error(f"Error reading tree file {tree_file_path}: {e}")
        return None, None, None, None, None, []

    return (
        source_dir_in_file,
        output_file_in_file,
        extension_in_file,
        remove_comments_in_file,
        remove_docstrings_in_file,
        included_paths,
    )
