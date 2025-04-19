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
        super().__init__(label=directory.name, **kwargs)
        self.root_directory = directory
        self.extension = extension
        self.hide_patterns = hide_patterns or []
        self.select_patterns = select_patterns or []
        self.selected_files: Set[str] = set()
        self.file_nodes: Dict[str, TreeNode] = {}
        self.expand()
        
        # Set up initial tree
        self.root.data = {"path": str(directory), "is_dir": True, "selected": False}
        self.populate_tree(self.root, directory)

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
                key=lambda p: (not p.is_dir(), p.name.lower())
            )
            
            for path in paths:
                # Skip hidden files and directories that start with .
                if path.name.startswith("."):
                    continue
                    
                # Skip paths that match hide patterns
                if any(fnmatch.fnmatch(path.name, pattern) for pattern in self.hide_patterns):
                    continue
                
                is_dir = path.is_dir()
                rel_path = path.relative_to(self.root_directory)
                
                # Skip directories that match hide patterns
                if is_dir and any(
                    fnmatch.fnmatch(str(rel_path) + "/", pattern) 
                    for pattern in self.hide_patterns
                ):
                    continue
                    
                # Only include the file if it has the right extension
                if not is_dir and not path.name.endswith(self.extension):
                    continue
                    
                # Create the label with appropriate icon
                icon = "📁 " if is_dir else "📄 "
                label = Text(f"{icon}{path.name}")
                
                # Create the node
                node = parent.add(
                    label,
                    data={"path": str(path), "is_dir": is_dir, "selected": False},
                )
                
                # Store file nodes for later lookup
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
        expanded_nodes = {node.data["path"] for node in self.walk_tree() 
                          if node.is_expanded and node.data.get("is_dir", False)}
        
        # Clear and rebuild the tree
        self.root.remove_children()
        self.file_nodes.clear()
        self.selected_files.clear()
        self.populate_tree(self.root, self.root_directory)
        
        # Restore selection state
        for file_path in selected_files:
            if file_path in self.file_nodes:
                node = self.file_nodes[file_path]
                node.data["selected"] = True
                self.selected_files.add(file_path)
                node.label = self._get_label_with_selection(node)
        
        # Restore expansion state
        for node in self.walk_tree():
            if node.data.get("is_dir", False) and node.data["path"] in expanded_nodes:
                node.expand()
        
        # Notify about selection
        self.post_message(self.FileSelected(self.selected_files.copy()))

    def walk_tree(self):
        """Walk through all nodes in the tree."""
        yield self.root
        yield from self._walk_node(self.root)
        
    def _walk_node(self, node):
        """Recursively walk through a node's children."""
        for child in node.children:
            yield child
            yield from self._walk_node(child)

    def _get_label_with_selection(self, node: TreeNode) -> Text:
        """Get the node label with selection indicator."""
        path = Path(node.data["path"])
        is_dir = node.data["is_dir"]
        is_selected = node.data["selected"]
        
        icon = "📁 " if is_dir else "📄 "
        select_icon = "[green]✓ " if is_selected else ""
        
        label = Text(f"{select_icon}{icon}{path.name}")
        if is_selected:
            label.stylize("bold green")
        return label

    def toggle_selection(self, node: TreeNode) -> None:
        """Toggle selection state for a node.
        
        Args:
            node: The node to toggle
        """
        if node.data.get("is_dir", False):
            # Toggle selection for all child files
            is_selected = not self._any_child_selected(node)
            self._select_node_children(node, is_selected)
        else:
            # Toggle selection for a single file
            path = node.data["path"]
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
        """Check if any child of the node is selected.
        
        Args:
            node: The node to check
            
        Returns:
            True if any child is selected, False otherwise
        """
        if not node.data.get("is_dir", False):
            return node.data.get("selected", False)
            
        for child in node.children:
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
        for child in node.children:
            if child.data.get("is_dir", False):
                self._select_node_children(child, select)
            else:
                path = child.data["path"]
                child.data["selected"] = select
                
                if select:
                    self.selected_files.add(path)
                else:
                    self.selected_files.discard(path)
                
                # Update node label
                child.label = self._get_label_with_selection(child)

    @on(Tree.NodeSelected)
    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle node selection events."""
        node = event.node
        
        # Toggle selection on space key or store current selection for navigation
        if self._last_key_press == " ":
            self.toggle_selection(node)
            
    @on(Tree.NodeHighlighted)
    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Track highlighted nodes for keyboard navigation."""
        self._highlighted_node = event.node
        
    async def on_key(self, event) -> None:
        """Handle key press events for the tree."""
        self._last_key_press = event.key
        
        # Handle space key for selection toggling
        if event.key == " " and self._highlighted_node:
            event.prevent_default()
            self.toggle_selection(self._highlighted_node)