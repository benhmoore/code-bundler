# Refactor CodeBundler CLI to TUI Application

### 1\. Introduce a TUI Framework

  * **What:** Add a dependency on a suitable TUI framework. `textual` is a strong candidate as it builds upon `rich`, which is already used for styling in `utils/helpers.py`.
  * **Where:** Update `setup.py` or `pyproject.toml` (whichever manages dependencies) to include the chosen library (e.g., `textual`). Install the dependency in the development environment.
  * **Why:** The current `rich`-based CLI doesn't support persistent, interactive widgets like a navigable directory tree or real-time updates needed for the envisioned workflow. A dedicated TUI framework provides the necessary components and event loop.

### 2\. Refactor Command-Line Argument Parsing (`codebundler/cli/commands.py`)

  * **What:** Modify the `argparse` setup in `setup_parser`.
      * Replace positional arguments `source_dir` and `output_file` with required flags like `--watch-path` and `--output`.
      * Add flags for the new features:
          * `--hide-patterns`: List of glob patterns (like `__pycache__/`, `*.meta`) to hide from the tree view. This can augment or replace existing `--ignore-names` and `--ignore-paths`.
          * `--select-patterns`: List of glob patterns (like `*.py`, `docs/*.md`) for initial file selection in the tree.
          * `--confirm-selection`: A boolean flag (default: True) to require user confirmation in the TUI before the initial bundle/watch. If False, start immediately.
      * The `--watch` flag will now primarily signal launching the TUI interface instead of the background-only watcher.
      * Remove `--interactive`, as the TUI becomes the main interactive mode.
      * Deprecate or adapt `--export-tree` and `--use-tree`. The TUI handles selection dynamically. Consider retaining them as optional features for saving/loading selection states if desired.
  * **Where:** `codebundler/cli/commands.py` -\> `setup_parser()` and `main()` functions.
  * **Why:** To provide the TUI application with the necessary configuration (target directory, output file, initial filters, startup behavior) directly from the command line.

### 3\. Create the Main TUI Application (New Module/Files)

  * **What:** Implement the main TUI application class (e.g., `class CodeBundlerApp(textual.app.App):`). This class will:
      * Initialize based on the parsed command-line arguments.
      * Set up the main layout (e.g., using `textual` containers).
      * Instantiate and manage the directory tree widget and potentially status bars or log views.
      * Handle global key bindings (e.g., quit).
      * Orchestrate interactions between the tree widget, file watcher, and bundler.
  * **Where:** Create a new file, e.g., `codebundler/tui/app.py`. The `main` function in `cli/commands.py` will instantiate and run this app when `--watch` (or similar) is used.
  * **Why:** To provide the central structure and control logic for the interactive user interface.

### 4\. Implement the Interactive Directory Tree Widget (New Module/Files)

  * **What:** Create a custom TUI widget, likely subclassing a tree widget from the chosen framework (e.g., `textual.widgets.Tree`). This widget must:
      * **Populate:** Scan the `--watch-path` recursively, applying `--hide-patterns` to filter what's displayed. Use file system APIs (like `os.scandir` or `pathlib.Path.iterdir`).
      * **Display:** Show directories and files, potentially using different icons or styles. Mark initially selected items based on `--select-patterns`.
      * **State:** Maintain the selection state (checked/unchecked) for each visible node (file/directory).
      * **Navigation:** Bind keys (Up/Down arrows) to move the focus. Bind keys (e.g., Left/Right arrows or Enter) to collapse/expand directories.
      * **Selection:** Bind a key (e.g., Spacebar) to toggle the selection state of the focused item. Selecting/deselecting a directory should cascade to all its (currently visible and valid) children. Implement multi-select (e.g., select all, clear all).
      * **Subdirectory Focus:** Implement a key (e.g., Enter/Right on a directory) to change the tree's root to that directory, effectively "zooming in". Implement a key (e.g., Backspace/Left) to navigate back up.
      * **Updates:** Provide methods to add, remove, or refresh nodes based on file system events.
  * **Where:** Create a new file, e.g., `codebundler/tui/widgets/directory_tree.py`. Instantiate this widget within the `CodeBundlerApp`.
  * **Why:** This is the core interactive element, allowing the user to visualize the file structure and define the bundle contents dynamically.

### 5\. Integrate File System Watching (`codebundler/utils/watcher.py` & TUI App)

  * **What:** Modify or reuse the existing `watchdog` setup.
      * The watcher needs to run in a separate thread managed by the TUI application.
      * Instead of a simple callback, events detected by `CodeBundlerHandler` should be posted to the TUI application's event queue (e.g., using `textual`'s `call_later` or custom messages).
      * The TUI app will receive these events and delegate updates to the `DirectoryTree` widget (e.g., `tree.add_node`, `tree.remove_node`).
      * File system changes should also trigger a rebundle operation *if* the changed file is relevant to the current selection.
  * **Where:** `codebundler/utils/watcher.py` might need changes to communicate with the TUI app's event loop. The TUI app (`codebundler/tui/app.py`) will manage the watcher's lifecycle and handle its events.
  * **Why:** To automatically detect external changes to the file system and reflect them in the TUI and the bundle in real-time.

### 6\. Adapt Bundling Logic (`codebundler/core/combiner.py`)

  * **What:** Modify the bundling functions to work with the TUI's dynamic selection.
      * The primary input should become the list of currently selected file paths obtained from the `DirectoryTree` widget's state.
      * The `combine_from_filelist` function is a good candidate for adaptation, as it already takes a list of files. Ensure it reads the latest transformation settings (strip comments/docstrings) potentially also managed by the TUI state.
      * The bundling process must run asynchronously (e.g., using `textual`'s `@work` decorator or `asyncio`) to avoid freezing the TUI.
      * The TUI app should trigger this bundling function:
          * Initially (after confirmation or immediately).
          * Whenever the selection changes in the `DirectoryTree`.
          * When the file watcher reports a relevant change.
  * **Where:** `codebundler/core/combiner.py`. The TUI app (`codebundler/tui/app.py`) will call the adapted bundling function.
  * **Why:** To connect the user's interactive selection and file system events directly to the core file combination logic, enabling immediate updates to the output bundle.

### 7\. Implement Real-Time Feedback

  * **What:** Provide visual feedback within the TUI.
      * Add a status bar or log area widget to the TUI layout.
      * Display messages like "Scanning directory...", "Watching for changes...", "Bundling...", "Bundle updated: \<output\_file\>", "Error: \<message\>".
      * Update the status when the bundler starts/finishes/errors and when file changes are detected.
  * **Where:** Within the TUI app (`codebundler/tui/app.py`) and its layout. The bundler and watcher integration points should update the status.
  * **Why:** To keep the user informed about the application's state and ongoing processes.

This refactor focuses on creating a dedicated TUI application that takes over the interactive aspects, managing the directory view, selection state, file watching, and triggering the existing (but adapted) bundling core logic.