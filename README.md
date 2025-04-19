# Code Bundler

A text-based UI (TUI) tool for combining and transforming source code files for large language model (LLM) usage.

## Overview

Code Bundler helps developers package multiple source code files into a single consolidated file for sharing with LLMs like Claude, ChatGPT, or other AI assistants. It features:

- Interactive TUI (Text User Interface) for intuitive file selection
- Support for any file type with customizable selection patterns
- Source code transformations (comment and docstring removal)
- Real-time file monitoring and automatic rebuilding
- Clipboard integration for easy sharing with LLMs

## Installation

```bash
pip install codebundler
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

## Keyboard Controls

| Key | Action |
|-----|--------|
| Space/Enter | Toggle selection of current node |
| a | Select all files |
| n | Deselect all files |
| r | Rebuild the bundle |
| c | Copy bundle to clipboard |
| h | Show/hide help screen |
| q | Quit the application |

## Mouse Controls

- **Click directories**: Expand/collapse directories
- **Click files**: Toggle file selection

## Examples

**Basic Usage**:
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

- **Interactive File Selection**: Select files with keyboard or mouse
- **Empty Directory Support**: Select/deselect empty directories
- **Multi-select**: Select multiple files across the project 
- **Transformation**: Optionally remove comments and docstrings
- **Live Monitoring**: Automatically rebuild when selected files change
- **Clipboard Integration**: Copy output directly to clipboard
- **Format Awareness**: Maintains correct comment prefixes based on file extensions
- **In-app Help**: Press 'h' to view all keyboard shortcuts

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.