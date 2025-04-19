# Code Bundler TUI Refactor - Todo List

Here are the tasks involved in refactoring the `code-bundler` to use an interactive TUI:

-   [x] **1. Introduce TUI Framework:**
    -   [x] Choose a TUI framework (e.g., `textual`).
    -   [x] Add the chosen framework as a project dependency.
    -   [x] Update `setup.py` or `pyproject.toml`.
    -   [x] Install the dependency in the development environment.

-   [ ] **2. Refactor CLI Argument Parsing (`codebundler/cli/commands.py`):**
    -   [ ] Replace positional `source_dir`, `output_file` with flags (`--watch-path`, `--output`).
    -   [ ] Add new flags: `--hide-patterns`, `--select-patterns`, `--confirm-selection`.
    -   [ ] Modify `--watch` flag behaviour to launch the TUI.
    -   [ ] Remove `--interactive` flag.
    -   [ ] Deprecate or adapt `--export-tree` / `--use-tree`.

-   [ ] **3. Create Main TUI Application (New Module/Files):**
    -   [ ] Create a new module (e.g., `codebundler/tui/`).
    -   [ ] Implement the main TUI application class (e.g., `tui/app.py`).
    -   [ ] Initialize the app using parsed CLI arguments.
    -   [ ] Set up the main TUI layout.
    -   [ ] Manage TUI widgets (Tree, Status Bar).
    -   [ ] Handle global key bindings.
    -   [ ] Modify `cli/commands.py` `main()` to launch the TUI app.

-   [ ] **4. Implement Interactive Directory Tree Widget (New Module/Files):**
    -   [ ] Create a custom Tree widget (e.g., `tui/widgets/directory_tree.py`).
    -   [ ] Implement directory scanning and population logic (respecting `--hide-patterns`).
    -   [ ] Implement display logic (icons, styles, initial selection based on `--select-patterns`).
    -   [ ] Implement selection state management (checked/unchecked).
    -   [ ] Implement keyboard navigation (Up/Down/Left/Right/Enter).
    -   [ ] Implement selection toggling (Spacebar, cascade selection for directories).
    -   [ ] Implement subdirectory focusing ("zooming").
    -   [ ] Implement methods for dynamic updates (add/remove/refresh nodes).

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
