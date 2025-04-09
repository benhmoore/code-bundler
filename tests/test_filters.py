"""Tests for the filters module."""

import unittest

from codebundler.core.filters import should_ignore, should_include


class TestFilters(unittest.TestCase):
    """Test cases for the filters module."""

    def test_should_include_empty_list(self):
        """Test that all files are included when the include list is empty."""
        self.assertTrue(should_include("file.py", []))
        self.assertTrue(should_include("test_file.py", []))

    def test_should_include_with_keywords(self):
        """Test including files based on keywords."""
        include_names = ["main", "utils"]
        self.assertTrue(should_include("main.py", include_names))
        self.assertTrue(should_include("utils.py", include_names))
        self.assertTrue(should_include("app_main.py", include_names))
        self.assertFalse(should_include("test.py", include_names))

    def test_should_ignore_by_name(self):
        """Test ignoring files by name."""
        ignore_names = ["test_", "__pycache__"]
        ignore_paths = []

        self.assertTrue(
            should_ignore(
                "test_file.py", "path/to/test_file.py", ignore_names, ignore_paths
            )
        )
        self.assertTrue(
            should_ignore(
                "__pycache__.py", "path/to/__pycache__.py", ignore_names, ignore_paths
            )
        )
        self.assertFalse(
            should_ignore("main.py", "path/to/main.py", ignore_names, ignore_paths)
        )

    def test_should_ignore_by_path(self):
        """Test ignoring files by path."""
        ignore_names = []
        ignore_paths = ["/tests/", "/build/"]

        self.assertTrue(
            should_ignore("file.py", "path/tests/file.py", ignore_names, ignore_paths)
        )
        self.assertTrue(
            should_ignore("file.py", "path/build/file.py", ignore_names, ignore_paths)
        )
        self.assertFalse(
            should_ignore("file.py", "path/src/file.py", ignore_names, ignore_paths)
        )

    def test_should_ignore_combined(self):
        """Test ignoring files with both name and path criteria."""
        ignore_names = ["test_"]
        ignore_paths = ["/build/"]

        self.assertTrue(
            should_ignore(
                "test_file.py", "path/src/test_file.py", ignore_names, ignore_paths
            )
        )
        self.assertTrue(
            should_ignore("file.py", "path/build/file.py", ignore_names, ignore_paths)
        )
        self.assertFalse(
            should_ignore("file.py", "path/src/file.py", ignore_names, ignore_paths)
        )


if __name__ == "__main__":
    unittest.main()
