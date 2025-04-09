"""Main entry point for the package when run as a module."""

import sys

from codebundler.cli.commands import main

if __name__ == "__main__":
    sys.exit(main())
