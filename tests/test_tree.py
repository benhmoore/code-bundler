"""Tests for the tree module."""

import os
import tempfile
import unittest
from pathlib import Path

from codebundler.core.tree import generate_tree_file, parse_tree_file


class TestTree(unittest.TestCase):
    """Test cases for the tree module."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name)

        # Create a simple directory structure
        (self.source_dir / "src").mkdir()
        (self.source_dir / "tests").mkdir()
        (self.source_dir / "docs").mkdir()

        # Create some test files
        (self.source_dir / "src" / "main.py").touch()
        (self.source_dir / "src" / "utils.py").touch()
        (self.source_dir / "tests" / "test_main.py").touch()
        (self.source_dir / "README.md").touch()

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_generate_tree_file(self):
        """Test generating a tree file."""
        # Create a temporary file for the tree output
        with tempfile.NamedTemporaryFile(delete=False) as tree_file:
            tree_path = tree_file.name

        try:
            # Generate the tree file
            file_count = generate_tree_file(
                source_dir=str(self.source_dir),
                tree_output_path=tree_path,
                extension=".py",
                ignore_names=[],
                ignore_paths=[],
                include_names=[],
                output_file="output.py",
                remove_comments=True,
                remove_docstrings=True,
            )

            # Check that the file was created
            self.assertTrue(os.path.exists(tree_path))

            # Check that we found the expected number of .py files
            self.assertEqual(file_count, 3)

            # Read the tree file and check its content
            with open(tree_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for header information
            self.assertIn(f"# Source Directory: {self.source_dir}", content)
            self.assertIn("# Output File: output.py", content)
            self.assertIn("# Extension: .py", content)
            self.assertIn("# Strip Comments: yes", content)
            self.assertIn("# Remove Docstrings: yes", content)

            # Check for the expected files
            self.assertIn("main.py", content)
            self.assertIn("utils.py", content)
            self.assertIn("test_main.py", content)

        finally:
            # Clean up
            if os.path.exists(tree_path):
                os.unlink(tree_path)

    def test_parse_tree_file(self):
        """Test parsing a tree file."""
        # Create a tree file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, encoding="utf-8"
        ) as tree_file:
            tree_file.write(f"# Source Directory: {self.source_dir}\n")
            tree_file.write("# Output File: output.py\n")
            tree_file.write("# Extension: .py\n")
            tree_file.write("# Strip Comments: yes\n")
            tree_file.write("# Remove Docstrings: no\n")
            tree_file.write("# Proposed inclusion list...\n\n")
            tree_file.write("├── src\n")
            tree_file.write("│   ├── main.py\n")
            tree_file.write("│   └── utils.py\n")
            tree_file.write("└── tests\n")
            tree_file.write("    └── test_main.py\n")

            tree_path = tree_file.name

        try:
            # Parse the tree file
            (
                source_dir,
                output_file,
                extension,
                remove_comments,
                remove_docstrings,
                included_paths,
            ) = parse_tree_file(tree_path)

            # Check the parsed values
            self.assertEqual(source_dir, str(self.source_dir))
            self.assertEqual(output_file, "output.py")
            self.assertEqual(extension, ".py")
            self.assertEqual(remove_comments, True)
            self.assertEqual(remove_docstrings, False)

            # Check that we found the expected files
            expected_files = ["src/main.py", "src/utils.py", "tests/test_main.py"]
            # Note that directories are also included
            expected_dirs = ["src", "tests"]

            # Check each expected file is in the included paths
            for file in expected_files:
                self.assertIn(file, included_paths)

            # Check each expected directory is in the included paths
            for directory in expected_dirs:
                self.assertIn(directory, included_paths)

        finally:
            # Clean up
            if os.path.exists(tree_path):
                os.unlink(tree_path)


if __name__ == "__main__":
    unittest.main()
