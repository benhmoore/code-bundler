"""File combining operations."""

import logging
import os
from pathlib import Path
from typing import Callable, List, Optional

from codebundler.core.filters import should_ignore, should_include
from codebundler.core.transformers import apply_transformations, get_comment_prefix

logger = logging.getLogger(__name__)


def combine_from_filelist(
    source_dir: str,
    output_file: str,
    extension: str,
    filelist: List[str],
    remove_comments: bool = False,
    remove_docstrings: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> int:
    """
    Combine files from a list into a single output file.

    Args:
        source_dir: Source directory
        output_file: Output file path
        extension: File extension
        filelist: List of file paths to include
        remove_comments: Whether to remove comments
        remove_docstrings: Whether to remove docstrings
        progress_callback: Optional callback function to report progress

    Returns:
        Number of files processed
    """
    comment_prefix = get_comment_prefix(extension)
    processed_count = 0

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(
            f"{comment_prefix} Files combined from the manually edited tree.\n\n"
        )

        for rel_path in filelist:
            if not rel_path.endswith(extension):
                continue

            abs_path = os.path.join(source_dir, rel_path)
            if not os.path.isfile(abs_path):
                logger.warning(f"File not found: {abs_path}")
                continue

            # Report progress if callback is provided
            if progress_callback:
                progress_callback(rel_path)

            try:
                with open(abs_path, "r", encoding="utf-8") as infile:
                    lines = infile.readlines()
            except UnicodeDecodeError:
                logger.warning(f"Could not read file as UTF-8: {abs_path}")
                continue
            except Exception as e:
                logger.warning(f"Error reading file {abs_path}: {e}")
                continue

            lines = apply_transformations(
                lines,
                extension,
                remove_comments=remove_comments,
                remove_docstrings=remove_docstrings,
            )

            header = f"{comment_prefix} ==== BEGIN FILE: {rel_path} ====\n"
            footer = f"\n{comment_prefix} ==== END FILE: {rel_path} ====\n\n"

            outfile.write(header)
            outfile.writelines(lines)
            outfile.write(footer)
            processed_count += 1
            logger.debug(f"Processed file: {rel_path}")

    return processed_count


def combine_source_files(
    source_dir: str,
    output_file: str,
    extension: str,
    ignore_names: Optional[List[str]] = None,
    ignore_paths: Optional[List[str]] = None,
    include_names: Optional[List[str]] = None,
    remove_comments: bool = False,
    remove_docstrings: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> int:
    """
    Combine source files by walking the directory tree.

    Args:
        source_dir: Source directory
        output_file: Output file path
        extension: File extension
        ignore_names: List of keywords to ignore in filenames
        ignore_paths: List of keywords to ignore in paths
        include_names: List of keywords to match in filenames
        remove_comments: Whether to remove comments
        remove_docstrings: Whether to remove docstrings
        progress_callback: Optional callback function to report progress

    Returns:
        Number of files processed
    """
    ignore_names = ignore_names or []
    ignore_paths = ignore_paths or []
    include_names = include_names or []

    comment_prefix = get_comment_prefix(extension)
    processed_count = 0

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(f"{comment_prefix} Combined files from: {source_dir}\n\n")

        # First, collect all matching files
        matching_files = []
        for root, _, files in os.walk(source_dir):
            for filename in sorted(files):
                if not filename.endswith(extension):
                    continue

                rel_path = os.path.relpath(os.path.join(root, filename), source_dir)
                rel_path = rel_path.replace("\\", "/")

                if should_ignore(filename, rel_path, ignore_names, ignore_paths):
                    logger.debug(f"Ignoring file: {rel_path}")
                    continue
                if not should_include(filename, include_names):
                    logger.debug(f"Skipping file (not in include list): {rel_path}")
                    continue

                matching_files.append((root, filename, rel_path))

        # Now process each file
        for root, filename, rel_path in matching_files:
            # Report progress if callback is provided
            if progress_callback:
                progress_callback(rel_path)

            abs_path = os.path.join(root, filename)

            try:
                with open(abs_path, "r", encoding="utf-8") as infile:
                    lines = infile.readlines()
            except UnicodeDecodeError:
                logger.warning(f"Could not read file as UTF-8: {abs_path}")
                continue
            except Exception as e:
                logger.warning(f"Error reading file {abs_path}: {e}")
                continue

            lines = apply_transformations(
                lines,
                extension,
                remove_comments=remove_comments,
                remove_docstrings=remove_docstrings,
            )

            header = f"{comment_prefix} ==== BEGIN FILE: {rel_path} ====\n"
            footer = f"\n{comment_prefix} ==== END FILE: {rel_path} ====\n\n"

            outfile.write(header)
            outfile.writelines(lines)
            outfile.write(footer)
            processed_count += 1
            logger.debug(f"Processed file: {rel_path}")

    return processed_count
