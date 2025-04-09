# Code Bundler

A specialized tool for combining source code files into a single bundled file, designed specifically for use with Large Language Models (LLMs).

## Features

-   Combines multiple source code files into a single file
-   Intelligent filtering of files based on patterns
-   Tree-based file inclusion for precise control
-   Optional removal of comments and docstrings
-   Watch mode for automatic rebuilding on file changes
-   Cross-platform support

## Installation

```bash
pip install codebundler
```

## Usage

### Basic Usage

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py
```

### Filtering Files

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py --ignore-names "test_*.py,*_test.py" --ignore-paths "**/tests/**"
```

### Using a Tree File

Create a text file with a list of files to include, one per line:

```
src/main.py
src/utils/helpers.py
src/models/user.py
```

Then use it with the `--use-tree` flag:

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py --use-tree file_list.txt
```

### Removing Comments and Docstrings

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py --strip-comments --remove-docstrings
```

### Watch Mode

Watch for file changes and automatically rebuild the bundle:

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py --watch
```

This works with all other options, including tree files:

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py --use-tree file_list.txt --watch
```

Or with command-line filters:

```bash
codebundler --source-dir ./my_project --output-file bundled_code.py --ignore-paths "**/tests/**" --watch
```

Press Ctrl+C to stop the watch process.

## Command Line Options

| Option              | Description                                      |
| ------------------- | ------------------------------------------------ |
| --source-dir        | Source directory containing the code             |
| --output-file       | Output file path                                 |
| --ext               | File extension to include (default: .py)         |
| --ignore-names      | Comma-separated file patterns to ignore          |
| --ignore-paths      | Comma-separated path patterns to ignore          |
| --include-names     | Comma-separated file patterns to include         |
| --use-tree          | Use a tree file listing files to include         |
| --strip-comments    | Remove single and multi-line comments            |
| --remove-docstrings | Remove Python docstrings                         |
| --watch             | Watch for file changes and rebuild automatically |

## Example Use Cases

### Preparing Code for LLM Analysis

Bundle your codebase to send to ChatGPT or Claude for analysis:

```bash
codebundler --source-dir ./my_project --output-file for_llm.py --ignore-paths "**/tests/**,**/venv/**" --watch
```

### Creating a Single-File Version

Create a distributable single-file version of your multi-file application:

```bash
codebundler --source-dir ./my_app --output-file my_app_single_file.py --use-tree production_files.txt
```

## Notes

-   Watch mode uses debouncing to prevent excessive rebuilds when multiple files change simultaneously
-   For large projects, consider using more specific filters or a tree file to improve performance
