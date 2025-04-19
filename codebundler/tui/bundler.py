"""Bundling logic for the TUI."""

import logging
import os
from pathlib import Path
from typing import List, Optional

from codebundler.core.transformers import apply_transformations, get_comment_prefix

logger = logging.getLogger(__name__)


def create_bundle(
    source_dir: str,
    output_file: str,
    file_paths: List[str],
    extension: str,
    remove_comments: bool = False,
    remove_docstrings: bool = False,
) -> int:
    """
    Combine selected files into a single bundle.

    Args:
        source_dir: Root directory containing the source files
        output_file: Path to the output file
        file_paths: List of absolute file paths to include
        extension: File extension to use for comment formatting
        remove_comments: Whether to remove comments
        remove_docstrings: Whether to remove docstrings

    Returns:
        Number of files processed
    """
    comment_prefix = get_comment_prefix(extension)
    processed_count = 0

    # Create output directory if it doesn't exist
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as outfile:
        outfile.write(f"{comment_prefix} Files combined from: {source_dir}\n\n")

        for abs_path in file_paths:
            # Convert to relative path for better readability in the output
            rel_path = os.path.relpath(abs_path, source_dir)
            
            try:
                with open(abs_path, "r", encoding="utf-8") as infile:
                    lines = infile.readlines()
            except UnicodeDecodeError:
                logger.warning(f"Could not read file as UTF-8: {abs_path}")
                continue
            except Exception as e:
                logger.warning(f"Error reading file {abs_path}: {e}")
                continue

            # Apply transformations if requested
            lines = apply_transformations(
                lines,
                extension,
                remove_comments=remove_comments,
                remove_docstrings=remove_docstrings,
            )

            # Add file header and footer
            header = f"{comment_prefix} ==== BEGIN FILE: {rel_path} ====\n"
            footer = f"\n{comment_prefix} ==== END FILE: {rel_path} ====\n\n"

            outfile.write(header)
            outfile.writelines(lines)
            outfile.write(footer)
            processed_count += 1
            logger.debug(f"Processed file: {rel_path}")

    return processed_count