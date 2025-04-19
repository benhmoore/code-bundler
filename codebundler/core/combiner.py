"""File combining operations."""

import logging
import os
from pathlib import Path
from typing import Callable, List, Optional

from codebundler.core.filters import should_ignore, should_include
from codebundler.core.transformers import apply_transformations, get_comment_prefix

logger = logging.getLogger(__name__)


# Legacy combining functions have been removed
# TUI implementation now uses bundler.py instead
