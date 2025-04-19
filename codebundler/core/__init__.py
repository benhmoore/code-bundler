"""Core functionality for Code Bundler."""

# This makes imports cleaner for other modules
from codebundler.core.combiner import combine_from_filelist, combine_source_files
from codebundler.core.filters import should_ignore, should_include
from codebundler.core.transformers import (
    apply_transformations,
    get_comment_prefix,
    remove_python_docstrings,
    strip_single_line_comments,
)

__all__ = [
    "combine_from_filelist",
    "combine_source_files",
    "should_ignore",
    "should_include",
    "apply_transformations",
    "get_comment_prefix",
    "remove_python_docstrings",
    "strip_single_line_comments",
]
