# Code Bundler TUI Refactor - Todo List

Here are the tasks involved in refactoring the `code-bundler` to use an interactive TUI:

-   [x] **1. Introduce TUI Framework:**
    -   [x] Choose a TUI framework (e.g., `textual`).
    -   [x] Add the chosen framework as a project dependency.
    -   [x] Update `setup.py` or `pyproject.toml`.
    -   [x] Install the dependency in the development environment.

-   [x] **2. Refactor CLI Argument Parsing (`codebundler/cli/commands.py`):**
    -   [x] Replace positional `source_dir`, `output_file` with flags (`--watch-path`, `--output`).
    -   [x] Add new flags: `--hide-patterns`, `--select-patterns`, `--confirm-selection`.
    -   [x] Modify `--watch` flag behaviour to launch the TUI.
    -   [x] Update `--interactive` flag to be an alias for `--watch`.
    -   [x] Remove `--export-tree` / `--use-tree` functionality in favor of the TUI.

-   [x] **3. Create Main TUI Application (New Module/Files):**
    -   [x] Create a new module (e.g., `codebundler/tui/`).
    -   [x] Implement the main TUI application class (e.g., `tui/app.py`).
    -   [x] Initialize the app using parsed CLI arguments.
    -   [x] Set up the main TUI layout.
    -   [x] Manage TUI widgets (Tree, Status Bar).
    -   [x] Handle global key bindings.
    -   [x] Modify `cli/commands.py` `main()` to launch the TUI app.

-   [x] **4. Implement Interactive Directory Tree Widget (New Module/Files):**
    -   [x] Create a custom Tree widget (e.g., `tui/widgets/directory_tree.py`).
    -   [x] Implement directory scanning and population logic (respecting `--hide-patterns`).
    -   [x] Implement display logic (icons, styles, initial selection based on `--select-patterns`).
    -   [x] Implement selection state management (checked/unchecked).
    -   [x] Implement keyboard navigation (Up/Down/Left/Right/Enter).
    -   [x] Implement selection toggling (Spacebar, cascade selection for directories).
    -   [x] Implement subdirectory focusing ("zooming").
    -   [x] Implement methods for dynamic updates (add/remove/refresh nodes).

-   [x] **5. Integrate File System Watching (`codebundler/utils/watcher.py` & TUI App):**
    -   [x] Modify `watchdog` integration to run in a separate thread managed by the TUI app.
    -   [x] Change event handling to post events to the TUI app's event queue.
    -   [x] Implement event handling in the TUI app to update the `DirectoryTree` widget.
    -   [x] Trigger rebundling based on relevant file system events.

-   [x] **6. Adapt Bundling Logic (`codebundler/core/combiner.py`):**
    -   [x] Modify `combine_from_filelist` to work with the file list from the `DirectoryTree` state.
    -   [x] Ensure the bundling function uses current transformation settings (from TUI state).
    -   [x] Implement asynchronous execution for the bundling process (using `textual`'s `@work`).
    -   [x] Trigger the bundling function from the TUI app (on init, selection change, relevant file change).

-   [x] **7. Implement Real-Time Feedback:**
    -   [x] Add status bar/log widgets to the TUI layout.
    -   [x] Display status messages (Scanning, Watching, Bundling, Updated, Error).
    -   [x] Update status messages from the TUI app based on watcher and bundler events.
