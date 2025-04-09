# Code Bundler

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/codebundler)
![PyPI](https://img.shields.io/pypi/v/codebundler)
![PyPI - License](https://img.shields.io/pypi/l/codebundler)

Combine and transform source code files for LLM (Large Language Model) usage.

## Features

- **Export Mode**: Generate a tree of matching source files for review and selection
- **Select Mode**: Use a tree file to select specific files for inclusion
- **Direct Mode**: Combine source files in one pass
- **Filtering**: Filter files by name patterns or path segments
- **Transformations**: Optionally remove comments or docstrings

## Installation

```bash
pip install codebundler
```

## Usage

### Basic Usage

Combine all Python files in a directory:

```bash
codebundler /path/to/source output.py --ext .py
```

### Interactive Mode

Run in interactive mode for a guided experience:

```bash
codebundler -i
```

### Export a Tree File

Export a tree file to manually select which files to include:

```bash
codebundler /path/to/source --export-tree my_tree.txt --ext .py
```

Then edit the tree file, removing lines for files you don't want to include.

### Combine Using a Tree File

Use an edited tree file to combine selected files:

```bash
codebundler --use-tree my_tree.txt
```

### Additional Options

- `--ignore-names`: Ignore files containing these keywords
- `--ignore-paths`: Ignore paths containing these keywords
- `--include-names`: Only include files containing these keywords
- `--strip-comments`: Remove single-line comments
- `--remove-docstrings`: Remove docstrings (Python only)

## Examples

### Preparing code for an LLM session

```bash
# Export tree for review
codebundler ./my_project --export-tree project_tree.txt --ext .py --strip-comments

# Edit project_tree.txt to remove test files or other unwanted files

# Combine files using edited tree
codebundler --use-tree project_tree.txt
```

### Direct combination with filters

```bash
codebundler ./my_project combined.py --ext .py \
  --ignore-names test_ __pycache__ \
  --ignore-paths /tests/ /data/ \
  --strip-comments
```

## API Usage

You can also use Code Bundler programmatically:

```python
from codebundler import combine_source_files

combine_source_files(
    source_dir="./my_project",
    output_file="combined.py",
    extension=".py",
    ignore_names=["test_", "__pycache__"],
    ignore_paths=["/tests/", "/data/"],
    remove_comments=True
)
```

## License

MIT
