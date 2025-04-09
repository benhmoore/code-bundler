"""Tests for the transformers module."""

import unittest

from codebundler.core.transformers import (
    get_comment_prefix,
    remove_python_docstrings,
    strip_single_line_comments,
)


class TestTransformers(unittest.TestCase):
    """Test cases for the transformers module."""

    def test_get_comment_prefix(self):
        """Test getting comment prefixes for different extensions."""
        self.assertEqual(get_comment_prefix(".py"), "#")
        self.assertEqual(get_comment_prefix(".js"), "//")
        self.assertEqual(get_comment_prefix(".unknown"), "#")  # Default

    def test_strip_single_line_comments_python(self):
        """Test stripping Python single-line comments."""
        lines = [
            "# This is a comment\n",
            "def hello():\n",
            "    # This is another comment\n",
            "    print('Hello, world!')\n",
            "# One more comment\n",
        ]
        expected = [
            "def hello():\n",
            "    print('Hello, world!')\n",
        ]
        result = strip_single_line_comments(lines, ".py")
        self.assertEqual(result, expected)

    def test_strip_single_line_comments_js(self):
        """Test stripping JavaScript single-line comments."""
        lines = [
            "// This is a comment\n",
            "function hello() {\n",
            "    // This is another comment\n",
            "    console.log('Hello, world!');\n",
            "}\n",
            "// One more comment\n",
        ]
        expected = [
            "function hello() {\n",
            "    console.log('Hello, world!');\n",
            "}\n",
        ]
        result = strip_single_line_comments(lines, ".js")
        self.assertEqual(result, expected)

    def test_strip_single_line_comments_unknown_extension(self):
        """Test that unknown extensions don't have comments stripped."""
        lines = [
            "# This is a comment\n",
            "def hello():\n",
            "    # This is another comment\n",
            "    print('Hello, world!')\n",
        ]
        result = strip_single_line_comments(lines, ".unknown")
        self.assertEqual(result, lines)  # Should be unchanged

    def test_remove_python_docstrings_triple_quotes(self):
        """Test removing Python docstrings with triple double quotes."""
        lines = [
            "def hello():\n",
            '    """This is a docstring.\n',
            "    It spans multiple lines.\n",
            '    """\n',
            "    print('Hello, world!')\n",
        ]
        expected = [
            "def hello():\n",
            "    print('Hello, world!')\n",
        ]
        result = remove_python_docstrings(lines)
        self.assertEqual(result, expected)

    def test_remove_python_docstrings_triple_single_quotes(self):
        """Test removing Python docstrings with triple single quotes."""
        lines = [
            "def hello():\n",
            "    '''This is a docstring.\n",
            "    It spans multiple lines.\n",
            "    '''\n",
            "    print('Hello, world!')\n",
        ]
        expected = [
            "def hello():\n",
            "    print('Hello, world!')\n",
        ]
        result = remove_python_docstrings(lines)
        self.assertEqual(result, expected)

    def test_remove_python_docstrings_single_line(self):
        """Test removing single-line Python docstrings."""
        lines = [
            "def hello():\n",
            '    """This is a single-line docstring."""\n',
            "    print('Hello, world!')\n",
        ]
        expected = [
            "def hello():\n",
            "    print('Hello, world!')\n",
        ]
        result = remove_python_docstrings(lines)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
