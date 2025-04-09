"""Code Bundler - Combine and transform source code files for LLM usage."""

from importlib.metadata import version

try:
    __version__ = version("codebundler")
except Exception:
    __version__ = "unknown"

# Public API
from codebundler.core.combiner import combine_from_filelist, combine_source_files
from codebundler.core.transformers import apply_transformations, get_comment_prefix
from codebundler.core.tree import generate_tree_file, parse_tree_file

__all__ = [
    "combine_from_filelist",
    "combine_source_files",
    "generate_tree_file",
    "parse_tree_file",
    "apply_transformations",
    "get_comment_prefix",
]
