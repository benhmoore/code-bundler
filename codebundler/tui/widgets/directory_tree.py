"""Interactive directory tree widget for file selection."""

import fnmatch
import logging
import os
from pathlib import Path
from typing import Dict, List, Set

from rich.text import Text
from textual import on
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

logger = logging.getLogger(__name__)


class DirectoryTree(Tree):
    """A tree widget for navigating and selecting files in a directory structure."""

    class FileSelected(Message):
        """Message sent when file selection changes."""

        def __init__(self, selected_files: Set[str]) -> None:
            """Initialize with the set of selected files.

            Args:
                selected_files: Set of absolute paths to selected files
            """
            self.selected_files = selected_files
            super().__init__()

    def __init__(
        self,
        directory: Path,
        extension: str = ".py",
        hide_patterns: List[str] = None,
        select_patterns: List[str] = None,
        **kwargs,
    ) -> None:
        """Initialize the directory tree.

        Args:
            directory: Root directory to display
            extension: File extension to filter by
            hide_patterns: Glob patterns for files/dirs to hide from the tree
            select_patterns: Glob patterns for initial file selection
            **kwargs: Additional arguments for the Tree widget
        """
        # Initialize the tree with the root directory as the label
        super().__init__(str(directory.name), **kwargs)

        # Store configuration
        self.root_directory = directory
        self.extension = extension
        self.hide_patterns = hide_patterns or []
        self.select_patterns = select_patterns or []
        self.selected_files: Set[str] = set()
        self.file_nodes: Dict[str, TreeNode] = {}

        # Initialize trackers for key press handling
        self._last_key_press = None
        self._highlighted_node = None

        # ID is already set by super().__init__ through kwargs

    def on_mount(self) -> None:
        """Initialize the tree after the widget is mounted."""
        # Create the root node
        root_node = self.root.add(
            str(self.root_directory.name),
            data={"path": str(self.root_directory), "is_dir": True, "selected": False},
        )

        # Populate the tree
        self.populate_tree(root_node, self.root_directory)

        # Expand the root node
        root_node.expand()

    def populate_tree(self, parent: TreeNode, directory: Path) -> None:
        """Recursively populate the tree with nodes for files and directories.

        Args:
            parent: Parent node to populate under
            directory: Directory to scan
        """
        try:
            # Sort directories first, then files
            paths = sorted(
                list(directory.iterdir()),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )

            for path in paths:
                # Skip hidden files and directories that start with .
                if path.name.startswith("."):
                    continue

                # Skip paths that match hide patterns
                if any(
                    fnmatch.fnmatch(path.name, pattern)
                    for pattern in self.hide_patterns
                ):
                    continue

                is_dir = path.is_dir()
                rel_path = str(path.relative_to(self.root_directory))

                # Skip directories that match hide patterns
                if is_dir and any(
                    fnmatch.fnmatch(f"{rel_path}/", pattern)
                    for pattern in self.hide_patterns
                ):
                    continue

                # Include all files for selection - no extension filtering
                is_matching_file = True

                # Show all files and allow selection of any file type

                # Create the label with appropriate icon
                if is_dir:
                    icon = "📁 "
                    label = Text(f"{icon}{path.name}")
                else:
                    icon = "📄 "
                    label = Text(f"{icon}{path.name}")

                # Create the node - all files are selectable now
                if is_dir:
                    # Directories can be expanded
                    node = parent.add(
                        label,
                        data={
                            "path": str(path),
                            "is_dir": is_dir,
                            "selected": False,
                            "selectable": True,
                        },
                    )
                else:
                    # Files can't be expanded, so set allow_expand=False to hide the arrow
                    node = parent.add(
                        label,
                        data={
                            "path": str(path),
                            "is_dir": is_dir,
                            "selected": False,
                            "selectable": True,
                        },
                        allow_expand=False,  # No expansion arrows for files
                    )

                # Store file nodes for later lookup - track all files
                if not is_dir:
                    self.file_nodes[str(path)] = node

                # Recursively populate directories
                if is_dir:
                    self.populate_tree(node, path)

        except (PermissionError, FileNotFoundError) as e:
            logger.error(f"Error accessing directory {directory}: {e}")

    async def setup_initial_selection(self, patterns: List[str]) -> None:
        """Set up initial file selection based on patterns.

        Args:
            patterns: List of glob patterns to match
        """
        if not patterns:
            return

        for file_path, node in self.file_nodes.items():
            rel_path = os.path.relpath(file_path, str(self.root_directory))
            if any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns):
                node.data["selected"] = True
                self.selected_files.add(file_path)
                node.label = self._get_label_with_selection(node)

        # Notify about selection
        self.post_message(self.FileSelected(self.selected_files.copy()))

    def refresh_tree(self) -> None:
        """Refresh the tree to reflect file system changes."""
        # Save the current selection and expansion state
        selected_files = self.selected_files.copy()
        expanded_nodes = {
            node.data["path"]
            for node in self.walk_tree()
            if hasattr(node, "is_expanded")
            and node.is_expanded
            and node.data.get("is_dir", False)
        }

        # Clear and rebuild the tree
        self.root.remove_children()
        self.file_nodes.clear()
        self.selected_files.clear()

        # Recreate the root node
        root_node = self.root.add(
            str(self.root_directory.name),
            data={"path": str(self.root_directory), "is_dir": True, "selected": False},
        )

        # Repopulate
        self.populate_tree(root_node, self.root_directory)

        # Restore selection state
        for file_path in selected_files:
            if file_path in self.file_nodes:
                node = self.file_nodes[file_path]
                node.data["selected"] = True
                self.selected_files.add(file_path)
                node.label = self._get_label_with_selection(node)

        # Restore expansion state
        for node in self.walk_tree():
            if (
                node.data.get("is_dir", False)
                and node.data["path"] in expanded_nodes
                and hasattr(node, "expand")
            ):
                node.expand()

        # Notify about selection
        self.post_message(self.FileSelected(self.selected_files.copy()))

    def walk_tree(self):
        """Walk through all nodes in the tree."""
        yield self.root
        if hasattr(self.root, "children"):
            yield from self._walk_node(self.root)

    def _walk_node(self, node):
        """Recursively walk through a node's children."""
        if hasattr(node, "children"):
            for child in node.children:
                yield child
                yield from self._walk_node(child)

    def _get_label_with_selection(self, node: TreeNode) -> Text:
        """Get the node label with selection indicator."""
        if not hasattr(node, "data") or node.data is None:
            # For nodes without data, just return the original label
            return node.label if hasattr(node, "label") else Text(str(node))

        try:
            path = Path(node.data.get("path", "unknown"))
            is_dir = node.data.get("is_dir", False)
            is_selected = node.data.get("selected", False)

            # Create a simple label without rich text markup
            if is_selected:
                if is_dir:
                    label = Text("✓ 📁 ", style="green")
                else:
                    label = Text("✓ 📄 ", style="green")
                # Add the name in green
                label.append(path.name, style="green bold")
            else:
                # Unselected items
                if is_dir:
                    label = Text("  📁 ")
                else:
                    label = Text("  📄 ")
                # Add the name normally
                label.append(path.name)

            return label
        except Exception as e:
            self.log(f"Error creating label: {e}")
            return Text(str(node))

    def toggle_selection(self, node: TreeNode) -> None:
        """Toggle selection state for a node.

        Args:
            node: The node to toggle
        """
        # Check if the node has data
        if not hasattr(node, "data") or node.data is None:
            self.log(f"No data found for node: {node}")
            return

        try:
            # All nodes should be selectable now
            if node.data.get("is_dir", False):
                # Get the path of the directory
                dir_path = node.data.get("path", "")
                if not dir_path:
                    self.log(f"No path found for directory node: {node}")
                    return

                # Check if any child is selected
                has_selected_children = self._any_child_selected(node)

                # Toggle based on current selection state
                is_selected = not has_selected_children

                # Toggle selection for all child files
                self._select_node_children(node, is_selected)

                # For empty directories or directories with only subdirectories (no files)
                # we need to handle them specially to ensure they can be toggled
                if not hasattr(node, "children") or len(node.children) == 0:
                    # No children - add/remove directory itself to selection set
                    if is_selected:
                        self.selected_files.add(dir_path)
                    else:
                        self.selected_files.discard(dir_path)

                # Also mark the directory itself as selected/deselected for visual feedback
                node.data["selected"] = is_selected
                node.label = self._get_label_with_selection(node)
            else:
                # Toggle selection for a single file
                path = node.data.get("path", "")
                if not path:
                    self.log(f"No path found for node: {node}")
                    return

                is_selected = not node.data.get("selected", False)
                node.data["selected"] = is_selected

                if is_selected:
                    self.selected_files.add(path)
                else:
                    self.selected_files.discard(path)

                # Update node label to reflect selection state
                node.label = self._get_label_with_selection(node)

            # Notify about selection change
            self.post_message(self.FileSelected(self.selected_files.copy()))
        except Exception as e:
            self.log(f"Error toggling selection: {e}")

    def select_all_matching_files(self) -> None:
        """Select all files matching the extension filter."""
        for file_path, node in self.file_nodes.items():
            node.data["selected"] = True
            self.selected_files.add(file_path)
            node.label = self._get_label_with_selection(node)

        self.post_message(self.FileSelected(self.selected_files.copy()))

    def deselect_all_files(self) -> None:
        """Deselect all files in the tree."""
        for file_path, node in self.file_nodes.items():
            node.data["selected"] = False
            node.label = self._get_label_with_selection(node)

        self.selected_files.clear()
        self.post_message(self.FileSelected(self.selected_files.copy()))

    def _any_child_selected(self, node: TreeNode) -> bool:
        """Check if any child of the node is selected, or if the node itself is selected.

        Args:
            node: The node to check

        Returns:
            True if any child is selected or the node is selected, False otherwise
        """
        # Safety check for nodes without data
        if not hasattr(node, "data") or node.data is None:
            return False

        # If it's a file, check its own selection state
        if not node.data.get("is_dir", False):
            return node.data.get("selected", False)

        # For directories, we need to check a few cases
        path = node.data.get("path", "")

        # First check if the directory itself is directly in the selected_files
        if path in self.selected_files:
            return True

        # For empty directories, they should be selected if they're in the selected_files set
        if not hasattr(node, "children") or len(node.children) == 0:
            return path in self.selected_files

        # For non-empty directories, check all children
        if hasattr(node, "children"):
            for child in node.children:
                # Skip children without data
                if not hasattr(child, "data") or child.data is None:
                    continue

                if child.data.get("is_dir", False):
                    if self._any_child_selected(child):
                        return True
                elif child.data.get("selected", False):
                    return True

        return False

    def _select_node_children(self, node: TreeNode, select: bool) -> None:
        """Recursively select or deselect all file children of a node.

        Args:
            node: The parent node
            select: Whether to select (True) or deselect (False)
        """
        # For directories with no children, add the directory itself
        if not hasattr(node, "children") or len(node.children) == 0:
            # This is an empty directory - add/remove it from selection set
            dir_path = node.data.get("path", "")
            if dir_path:
                if select:
                    self.selected_files.add(dir_path)
                else:
                    self.selected_files.discard(dir_path)
            return

        # Handle children
        for child in node.children:
            # Skip children without data
            if not hasattr(child, "data") or child.data is None:
                continue

            try:
                # First update this child node's selection state
                child.data["selected"] = select

                # Update node label to reflect selection state
                child.label = self._get_label_with_selection(child)

                if child.data.get("is_dir", False):
                    # Check if this directory is empty
                    has_children = (
                        hasattr(child, "children") and len(child.children) > 0
                    )

                    if not has_children:
                        # This is an empty directory - add/remove it from selection set
                        dir_path = child.data.get("path", "")
                        if dir_path:
                            if select:
                                self.selected_files.add(dir_path)
                            else:
                                self.selected_files.discard(dir_path)
                    else:
                        # Recursively update all its children
                        self._select_node_children(child, select)
                else:
                    # This is a file - add/remove from selection set
                    path = child.data.get("path", "")
                    if not path:
                        continue

                    if select:
                        self.selected_files.add(path)
                    else:
                        self.selected_files.discard(path)
            except Exception as e:
                self.log(f"Error selecting child node: {e}")

    # Handle clicks - click on directory to expand/collapse, click on file to select
    async def on_click(self, event) -> None:
        """Handle click events on the tree."""
        try:
            # We need to identify which node was clicked
            # In Textual 3.1.0, this information is in the event's style metadata
            if hasattr(event, "style") and hasattr(event.style, "meta"):
                node_line = event.style.meta.get("line", None)

                if node_line is not None:
                    # Clear cached nodes to ensure we get fresh data
                    if hasattr(self, "_tree_nodes"):
                        delattr(self, "_tree_nodes")

                    # Get all visible nodes
                    nodes = list(self.nodes)

                    # Check if the line number is within range
                    if 0 <= node_line < len(nodes):
                        clicked_node = nodes[node_line]

                        # Now handle the node based on its type
                        if hasattr(clicked_node, "data") and clicked_node.data:
                            is_dir = clicked_node.data.get("is_dir", False)

                            if is_dir:
                                # For directories, toggle expansion
                                if hasattr(clicked_node, "is_expanded"):
                                    if clicked_node.is_expanded and hasattr(
                                        clicked_node, "collapse"
                                    ):
                                        await clicked_node.collapse()
                                    elif hasattr(clicked_node, "expand"):
                                        await clicked_node.expand()

                                # Clear the cache again after expansion changes
                                if hasattr(self, "_tree_nodes"):
                                    delattr(self, "_tree_nodes")
                            else:
                                # For files, toggle selection
                                event.prevent_default()  # Prevent default behavior
                                self.toggle_selection(clicked_node)

                        # Highlight the clicked node
                        self.select_node(clicked_node)
        except Exception as e:
            self.log(f"Error handling click: {e}")

    @property
    def nodes(self):
        """Get all visible nodes in the tree."""
        if hasattr(self, "_tree_nodes"):
            return self._tree_nodes

        nodes = []

        def collect_visible_nodes(node):
            nodes.append(node)
            if (
                hasattr(node, "is_expanded")
                and node.is_expanded
                and hasattr(node, "children")
            ):
                for child in node.children:
                    collect_visible_nodes(child)

        if hasattr(self.root, "children"):
            for child in self.root.children:
                collect_visible_nodes(child)

        self._tree_nodes = nodes
        return nodes

    # Keep this for handling keyboard selection
    @on(Tree.NodeSelected)
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection events from keyboard navigation."""
        # Just track the highlighted node - no selection happens here
        self._highlighted_node = event.node

    @on(Tree.NodeHighlighted)
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Track highlighted nodes for keyboard navigation."""
        self._highlighted_node = event.node

    @on(Tree.NodeExpanded)
    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Handle node expansion events."""
        # Clear the nodes cache since the tree structure changed
        if hasattr(self, "_tree_nodes"):
            delattr(self, "_tree_nodes")

    @on(Tree.NodeCollapsed)
    def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
        """Handle node collapse events."""
        # Clear the nodes cache since the tree structure changed
        if hasattr(self, "_tree_nodes"):
            delattr(self, "_tree_nodes")

    async def on_key(self, event) -> None:
        """Handle key press events for the tree."""
        self._last_key_press = event.key

        # Capture the currently highlighted node
        node = self._highlighted_node
        if not node:
            return

        try:
            # Handle space key for toggle selection (both files and directories)
            if event.key == " ":
                event.prevent_default()
                # Toggle selection for all node types
                self.toggle_selection(node)

                # Clear cached nodes to ensure we have the latest state
                if hasattr(self, "_tree_nodes"):
                    delattr(self, "_tree_nodes")

            # Handle enter key for selection ONLY (never expands/collapses)
            elif event.key == "enter":
                event.prevent_default()
                # Toggle selection for the highlighted node (either file or directory)
                self.toggle_selection(node)
        except Exception as e:
            self.log(f"Error handling key: {e} for {event.key}")
