"""Code Bundler - Combine and transform source code files for LLM usage."""

from importlib.metadata import version

try:
    __version__ = version("codebundler")
except Exception:
    __version__ = "unknown"

# Public API
from codebundler.core.transformers import apply_transformations, get_comment_prefix
from codebundler.tui.bundler import create_bundle

__all__ = [
    "create_bundle",
    "apply_transformations",
    "get_comment_prefix",
]
