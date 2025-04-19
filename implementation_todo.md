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
    -   [x] Update `--interactive` flag (marked as deprecated).
    -   [ ] Adapt `--export-tree` / `--use-tree` functionality in TUI.

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

-   [ ] **5. Integrate File System Watching (`codebundler/utils/watcher.py` & TUI App):**
    -   [ ] Modify `watchdog` integration to run in a separate thread managed by the TUI app.
    -   [ ] Change event handling to post events to the TUI app's event queue.
    -   [ ] Implement event handling in the TUI app to update the `DirectoryTree` widget.
    -   [ ] Trigger rebundling based on relevant file system events.

-   [ ] **6. Adapt Bundling Logic (`codebundler/core/combiner.py`):**
    -   [ ] Modify `combine_from_filelist` (or create a new function) to accept the file list directly from the `DirectoryTree` state.
    -   [ ] Ensure the bundling function uses current transformation settings (potentially from TUI state).
    -   [ ] Implement asynchronous execution for the bundling process (e.g., using `textual`'s `@work`).
    -   [ ] Trigger the bundling function from the TUI app (on init, selection change, relevant file change).

-   [ ] **7. Implement Real-Time Feedback:**
    -   [ ] Add status bar/log widgets to the TUI layout.
    -   [ ] Display status messages (Scanning, Watching, Bundling, Updated, Error).
    -   [ ] Update status messages from the TUI app based on watcher and bundler events.
