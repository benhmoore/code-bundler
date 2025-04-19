# Code Bundler

A tool for combining and transforming source code files for large language model (LLM) usage.

## Overview

Code Bundler helps developers package multiple source code files into a single consolidated file for sharing with LLMs like Claude, ChatGPT, or other AI assistants. It features:

- Interactive TUI (Text User Interface) for file selection
- Support for multiple file types
- Source code transformations (comment and docstring removal)
- Real-time file monitoring and automatic rebuilding

## Installation

```bash
pip install codebundler
```

For the full experience with the TUI interface:

```bash
pip install "codebundler[tui]"
```

## Usage

Code Bundler provides a TUI interface for selecting and bundling files:

```bash
codebundler /path/to/source/directory output.txt
```

### Command-line Options

- `--ignore=PATTERNS`: Comma-separated glob patterns to ignore (e.g., `__pycache__,*.meta`)
- `--select=PATTERNS`: Comma-separated glob patterns to select (e.g., `*.py,*.md`)
- `--strip-comments`: Remove single-line comments
- `--remove-docstrings`: Remove Python docstrings
- `--yes`: Skip confirmation and begin watching immediately
- `-v, --verbose`: Increase output verbosity (can be used multiple times)
- `-q, --quiet`: Suppress non-error output

## TUI Controls

- **Enter**: Toggle file selection
- **Space**: Expand/collapse directories
- **a**: Select all matching files
- **n**: Deselect all files
- **r**: Rebuild bundle
- **q**: Quit

## Examples

**Basic Usage (with TUI)**:
```bash
codebundler ./my-project output.txt
```

**Select only Python and Markdown files**:
```bash
codebundler ./my-project output.txt --select="*.py,*.md"
```

**Ignore specific directories and strip comments**:
```bash
codebundler ./my-project output.txt --ignore="node_modules,__pycache__" --strip-comments
```

## Features

- **File Selection**: Interactively select files for bundling with a keyboard-driven interface
- **Transformation**: Optionally remove comments and docstrings for more concise outputs
- **Watching**: Automatically rebuild the bundle when selected files change
- **Format Awareness**: Maintains correct comment prefixes based on file extensions

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.