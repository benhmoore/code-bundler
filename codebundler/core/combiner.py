"""File combining operations."""

import logging
import os
from pathlib import Path
from typing import Callable, List, Optional, Union

from codebundler.core.filters import (
    has_matching_extension,
    should_ignore,
    should_include,
)
from codebundler.core.transformers import apply_transformations, get_comment_prefix

logger = logging.getLogger(__name__)


def combine_from_filelist(
    source_dir: str,
    output_file: str,
    extensions: Union[str, List[str]],
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
        extensions: File extension(s) to include
        filelist: List of file paths to include
        remove_comments: Whether to remove comments
        remove_docstrings: Whether to remove docstrings
        progress_callback: Optional callback function to report progress

    Returns:
        Number of files processed
    """
    # Normalize extensions to a list
    if isinstance(extensions, str):
        extensions = [extensions]

    processed_count = 0

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as outfile:
        # Use comment prefix from the first extension as default for header
        comment_prefix = get_comment_prefix(extensions[0] if extensions else ".txt")
        outfile.write(
            f"{comment_prefix} Files combined from the manually edited tree.\n\n"
        )

        for rel_path in filelist:
            # Check if the file has one of the specified extensions
            if not has_matching_extension(rel_path, extensions):
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

            # Get the file's extension for proper comment handling
            _, file_extension = os.path.splitext(rel_path)

            lines = apply_transformations(
                lines,
                file_extension,
                remove_comments=remove_comments,
                remove_docstrings=remove_docstrings,
            )

            # Use the correct comment prefix based on the file's extension
            file_comment_prefix = get_comment_prefix(file_extension)
            header = f"{file_comment_prefix} ==== BEGIN FILE: {rel_path} ====\n"
            footer = f"\n{file_comment_prefix} ==== END FILE: {rel_path} ====\n\n"

            outfile.write(header)
            outfile.writelines(lines)
            outfile.write(footer)
            processed_count += 1
            logger.debug(f"Processed file: {rel_path}")

    return processed_count
