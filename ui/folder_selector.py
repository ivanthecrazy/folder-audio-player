import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

class FolderSelector(Gtk.Box):
    """UI component for selecting folders."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Add a section title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_start(10)
        title_box.set_margin_end(10)
        title_box.set_margin_top(10)
        title_box.set_margin_bottom(10)

        header_title = Gtk.Label()
        header_title.set_markup("<b>Folders</b>")
        header_title.set_halign(Gtk.Align.START)
        title_box.append(header_title)

        self.append(title_box)

        # Create a scrolled window for the folder tree
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(False)

        # Create a file tree for folder navigation
        self.file_store = Gtk.TreeStore(str, str)  # Display name, full path

        tree_view = Gtk.TreeView(model=self.file_store)
        tree_view.set_headers_visible(False)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Folder", renderer, text=0)
        tree_view.append_column(column)

        # Store the tree view for later access
        self.tree_view = tree_view

        scrolled.set_child(tree_view)
        self.append(scrolled)

        # Populate the file store
        self.populate_file_store()

    def populate_file_store(self):
        """Populate the file store with directories."""
        self.file_store.clear()

        # Add home directory
        home_dir = GLib.get_home_dir()
        home_iter = self.file_store.append(None, ["Home", home_dir])
        self.add_subdirectories(home_iter, home_dir)

        # Add root directory
        root_iter = self.file_store.append(None, ["Root", "/"])

        # Add common root directories
        try:
            for item in os.listdir("/"):
                full_path = os.path.join("/", item)
                if os.path.isdir(full_path) and not item.startswith('.'):
                    self.file_store.append(root_iter, [item, full_path])
        except PermissionError:
            pass  # Skip directories we can't access

        # Add media directory if it exists
        media_path = "/media"
        if os.path.exists(media_path) and os.path.isdir(media_path):
            media_iter = self.file_store.append(None, ["Media", media_path])
            self.add_subdirectories(media_iter, media_path)

    def add_subdirectories(self, parent_iter, parent_path, max_depth=1, current_depth=0):
        """Add subdirectories to the tree store."""
        if current_depth >= max_depth:
            return

        try:
            for item in os.listdir(parent_path):
                if item.startswith('.'):
                    continue

                full_path = os.path.join(parent_path, item)
                if os.path.isdir(full_path):
                    child_iter = self.file_store.append(parent_iter, [item, full_path])
                    # Add subdirectories recursively
                    self.add_subdirectories(child_iter, full_path, max_depth, current_depth + 1)
        except (PermissionError, FileNotFoundError):
            pass  # Skip directories we can't access

    def set_folder_selected_callback(self, callback):
        """Set callback for when a folder is selected."""
        self.tree_view.connect("row-activated", self._on_folder_selected, callback)

    def _on_folder_selected(self, tree_view, path, column, callback):
        """Handle folder selection."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        folder_path = model.get_value(iter, 1)

        if os.path.isdir(folder_path):
            callback(folder_path)

# This allows the file to be imported without running any code
if __name__ == "__main__":
    print("This module is not meant to be run directly.")
