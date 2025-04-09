"""Transformation operations for code files."""

import re
from typing import Dict, List, Optional

# Constants
COMMENT_SYNTAX: Dict[str, str] = {
    ".py": "#",
    ".cs": "//",
    ".js": "//",
    ".php": "//",
    ".java": "//",
    ".c": "//",
    ".cpp": "//",
    ".ts": "//",
    ".go": "//",
    ".rb": "#",
    ".rs": "//",
    ".swift": "//",
}


def get_comment_prefix(extension: str) -> str:
    """
    Get the comment prefix for a given file extension.

    Args:
        extension: File extension

    Returns:
        Comment prefix character(s)
    """
    return COMMENT_SYNTAX.get(extension, "#")


def strip_single_line_comments(lines: List[str], extension: str) -> List[str]:
    """
    Remove single-line comments from the source code.

    Args:
        lines: List of code lines
        extension: File extension to determine comment syntax

    Returns:
        List of lines with single-line comments removed
    """
    if extension not in COMMENT_SYNTAX:
        return lines

    if extension == ".py" or extension == ".rb":  # Python and Ruby
        pattern = re.compile(r"^\s*#")
    else:  # C-style languages
        pattern = re.compile(r"^\s*//")

    stripped_lines = []
    for line in lines:
        # Skip lines that match the single-line comment pattern
        if pattern.match(line):
            continue
        stripped_lines.append(line)

    return stripped_lines


def remove_python_docstrings(lines: List[str]) -> List[str]:
    """
    Remove triple-quote docstrings from Python code.

    Args:
        lines: List of Python code lines

    Returns:
        List of lines with docstrings removed
    """
    out = []
    inside_docstring = False
    quote_delimiter = None

    for line in lines:
        if inside_docstring:
            # Look for closing triple-quote
            if quote_delimiter in line:
                inside_docstring = False
                quote_delimiter = None
            continue

        # Not inside docstring: look for opening triple-quote
        matches = re.findall(r"('''|\"\"\")", line)
        if matches:
            # Simple heuristic: if there's a second instance of the delimiter on the same line,
            # it might be a single-line docstring, so we need to check if this is a complete docstring
            if matches[0] in line[line.find(matches[0]) + len(matches[0]) :]:
                # This is a single-line docstring, skip this line
                continue

            inside_docstring = True
            quote_delimiter = matches[0]
            continue

        out.append(line)

    return out


def apply_transformations(
    lines: List[str],
    extension: str,
    remove_comments: bool = False,
    remove_docstrings: bool = False,
) -> List[str]:
    """
    Apply a pipeline of transformations to the source code.

    Args:
        lines: List of code lines
        extension: File extension
        remove_comments: Whether to remove single-line comments
        remove_docstrings: Whether to remove docstrings (Python only)

    Returns:
        Transformed list of lines
    """
    if remove_docstrings and extension == ".py":
        lines = remove_python_docstrings(lines)
    if remove_comments:
        lines = strip_single_line_comments(lines, extension)
    return lines
