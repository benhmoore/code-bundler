"""Tests for the TUI bundler module."""

import os
import tempfile
import unittest
from pathlib import Path

from codebundler.tui.bundler import create_bundle


class TestBundler(unittest.TestCase):
    """Test cases for the TUI bundler module."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_dir = Path(self.temp_dir.name)

        # Create a simple directory structure
        (self.source_dir / "src").mkdir()
        (self.source_dir / "tests").mkdir()

        # Create some test files with content
        with open(self.source_dir / "src" / "main.py", "w", encoding="utf-8") as f:
            f.write("# Main module\n")
            f.write("def main():\n")
            f.write('    """Main function"""\n')
            f.write("    print('Hello, world!')\n")
            f.write("\n")
            f.write("if __name__ == '__main__':\n")
            f.write("    main()\n")

        with open(self.source_dir / "src" / "utils.py", "w", encoding="utf-8") as f:
            f.write("# Utilities module\n")
            f.write("def greet(name):\n")
            f.write('    """Greet a person"""\n')
            f.write("    return f'Hello, {name}!'\n")

        with open(
            self.source_dir / "tests" / "test_main.py", "w", encoding="utf-8"
        ) as f:
            f.write("# Test module\n")
            f.write("from src.main import main\n")
            f.write("\n")
            f.write("def test_main():\n")
            f.write("    # Test the main function\n")
            f.write("    main()\n")

        # Store absolute paths for testing
        self.all_files = [
            str(self.source_dir / "src" / "main.py"),
            str(self.source_dir / "src" / "utils.py"),
            str(self.source_dir / "tests" / "test_main.py"),
        ]

        self.src_files = [
            str(self.source_dir / "src" / "main.py"),
            str(self.source_dir / "src" / "utils.py"),
        ]

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_create_bundle_all_files(self):
        """Test bundling all files without transformations."""
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(delete=False) as output_file:
            output_path = output_file.name

        try:
            # Combine the files
            file_count = create_bundle(
                source_dir=str(self.source_dir),
                output_file=output_path,
                file_paths=self.all_files,
                remove_comments=False,
                remove_docstrings=False,
            )

            # Check that the output file was created
            self.assertTrue(os.path.exists(output_path))

            # Check that we processed the expected number of files
            self.assertEqual(file_count, 3)

            # Read the output file and check its content
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for file markers
            self.assertIn("# ==== BEGIN FILE: src/main.py ====", content)
            self.assertIn("# ==== END FILE: src/main.py ====", content)
            self.assertIn("# ==== BEGIN FILE: src/utils.py ====", content)
            self.assertIn("# ==== END FILE: src/utils.py ====", content)
            self.assertIn("# ==== BEGIN FILE: tests/test_main.py ====", content)
            self.assertIn("# ==== END FILE: tests/test_main.py ====", content)

            # Check that comments are preserved (since remove_comments=False)
            self.assertIn("# Main module", content)
            self.assertIn("# Utilities module", content)
            self.assertIn("# Test module", content)

            # Check that docstrings are preserved (since remove_docstrings=False)
            self.assertIn('"""Main function"""', content)
            self.assertIn('"""Greet a person"""', content)

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_create_bundle_with_transformations(self):
        """Test bundling files with transformations."""
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(delete=False) as output_file:
            output_path = output_file.name

        try:
            # Combine the files with transformations
            file_count = create_bundle(
                source_dir=str(self.source_dir),
                output_file=output_path,
                file_paths=self.all_files,
                remove_comments=True,
                remove_docstrings=True,
            )

            # Check that the output file was created
            self.assertTrue(os.path.exists(output_path))

            # Read the output file and check its content
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check that comments are removed
            self.assertNotIn("# Main module", content)
            self.assertNotIn("# Utilities module", content)
            self.assertNotIn("# Test module", content)
            self.assertNotIn("# Test the main function", content)

            # Check that docstrings are removed
            self.assertNotIn('"""Main function"""', content)
            self.assertNotIn('"""Greet a person"""', content)

            # But the code should still be there
            self.assertIn("def main():", content)
            self.assertIn("print('Hello, world!')", content)
            self.assertIn("def greet(name):", content)
            self.assertIn("return f'Hello, {name}!'", content)

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_create_bundle_subset_files(self):
        """Test bundling a subset of files."""
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(delete=False) as output_file:
            output_path = output_file.name

        try:
            # Combine only the src files
            file_count = create_bundle(
                source_dir=str(self.source_dir),
                output_file=output_path,
                file_paths=self.src_files,
                remove_comments=False,
                remove_docstrings=False,
            )

            # Check that the output file was created
            self.assertTrue(os.path.exists(output_path))

            # Check that we processed the expected number of files
            self.assertEqual(file_count, 2)

            # Read the output file and check its content
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for file markers for included files
            self.assertIn("# ==== BEGIN FILE: src/main.py ====", content)
            self.assertIn("# ==== END FILE: src/main.py ====", content)
            self.assertIn("# ==== BEGIN FILE: src/utils.py ====", content)
            self.assertIn("# ==== END FILE: src/utils.py ====", content)

            # Check that excluded files are not present
            self.assertNotIn("# ==== BEGIN FILE: tests/test_main.py ====", content)
            self.assertNotIn("# ==== END FILE: tests/test_main.py ====", content)

        finally:
            # Clean up
            if os.path.exists(output_path):
                os.unlink(output_path)


if __name__ == "__main__":
    unittest.main()
