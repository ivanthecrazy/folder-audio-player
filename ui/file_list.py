import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gdk, GdkPixbuf, Pango, Adw

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_file_type, is_audio_file, extract_album_art, get_audio_metadata, get_audio_duration, format_duration

class FileList(Gtk.Box):
    """UI component for displaying and selecting files."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_vexpand(True)

        # Add a section title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_start(10)
        title_box.set_margin_end(10)
        title_box.set_margin_top(10)
        title_box.set_margin_bottom(5)

        self.folder_title = Gtk.Label()
        self.folder_title.set_markup("<b>Files</b>")
        self.folder_title.set_halign(Gtk.Align.START)
        title_box.append(self.folder_title)

        self.append(title_box)

        # Create a scrolled window for the file list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)

        # Create a list store for the files
        # Columns: Pixbuf, Artist, Title, Full path, Is Playing, Duration
        self.list_store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str, bool, str)

        # Create a tree view for the file list
        self.tree_view = Gtk.TreeView(model=self.list_store)
        self.tree_view.set_headers_visible(False)

        # Create a default album art icon
        self.default_icon = self._create_default_icon()

        # Add a single column with a custom cell renderer
        renderer = Gtk.CellRendererPixbuf()
        renderer.set_property("xpad", 10)
        renderer.set_property("ypad", 5)

        text_renderer = Gtk.CellRendererText()
        text_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)

        # Duration renderer (right-aligned)
        duration_renderer = Gtk.CellRendererText()
        duration_renderer.set_property("xalign", 1.0)  # Right-align
        duration_renderer.set_property("yalign", 0.5)  # Vertically center
        duration_renderer.set_property("xpad", 10)     # Add padding

        column = Gtk.TreeViewColumn("Audio Files")
        column.pack_start(renderer, False)
        column.add_attribute(renderer, "pixbuf", 0)

        column.pack_start(text_renderer, True)
        column.set_cell_data_func(text_renderer, self._render_metadata)

        # Add duration renderer
        column.pack_end(duration_renderer, False)
        column.add_attribute(duration_renderer, "text", 5)  # Duration is at index 5

        column.set_expand(True)
        self.tree_view.append_column(column)

        scrolled.set_child(self.tree_view)
        self.append(scrolled)

        # Current folder and playlist
        self.current_folder = None
        self.playlist = []
        self.currently_playing = None

    def _create_default_icon(self):
        """Create a default album art icon."""
        # Create a default icon (music note or similar)
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

        # Print available icon theme paths for debugging
        print(f"Default icon - Icon theme search paths: {icon_theme.get_search_path()}")

        # Check if the icon exists in the theme
        icon_name = "audio-x-generic"
        has_icon = icon_theme.has_icon(icon_name)
        print(f"Default icon - Icon {icon_name} exists in theme: {has_icon}")

        try:
            icon = icon_theme.lookup_icon(icon_name, None, 32, 1, Gtk.TextDirection.NONE, 0)

            # In GTK 4, IconPaintable doesn't have load_icon method
            pixbuf = None

            # Try to get the pixbuf using the icon's storage type
            if hasattr(icon, 'get_file'):
                file = icon.get_file()
                if file:
                    path = file.get_path()
                    if path:
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)

            # If we couldn't get the pixbuf from the file, try other methods
            if pixbuf is None and hasattr(icon, 'get_paintable'):
                paintable = icon.get_paintable()
                # Convert paintable to pixbuf if possible
                # This would require additional code

            # If we still don't have a pixbuf, try the old method
            if pixbuf is None and hasattr(icon, 'load_icon'):
                pixbuf = icon.load_icon()

            if pixbuf is not None:
                print(f"Default icon - Successfully loaded icon: {icon_name}")
                return pixbuf
            else:
                raise Exception("Could not convert icon to pixbuf")
        except Exception as e:
            print(f"Default icon - Failed to load icon: {icon_name}, error: {e}")
            # Fallback if icon not found
            pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 32, 32)
            pixbuf.fill(0x33333399)  # Dark gray with some transparency
            return pixbuf

    def _render_metadata(self, column, cell, model, iter, data):
        """Custom renderer for displaying metadata."""
        artist = model.get_value(iter, 1)
        title = model.get_value(iter, 2)
        is_playing = model.get_value(iter, 4)

        # Check if this is the parent directory entry
        if title == "..":
            # For parent directory, make it visually distinct
            text = f'<span weight="bold" size="medium">..</span>'
            cell.set_property("xalign", 0.0)  # Left align horizontally
        # Check if this is a folder (empty artist field)
        elif not artist:
            # For folders, left align horizontally but keep centered vertically
            text = f'<span weight="bold" size="medium">{title}</span>'
            cell.set_property("xalign", 0.0)  # Left align horizontally
        else:
            # For audio files, format with artist on first line and title on second
            text = f"{artist}\n<b>{title}</b>"
            cell.set_property("xalign", 0.0)  # Left align

        # If this is the currently playing file, highlight it with system accent color
        if is_playing:
            # Get the accent color from the current theme
            style_manager = Adw.StyleManager.get_default()
            if style_manager.get_dark():
                # Use a brighter accent color for dark themes
                accent_color = "#78aeed"  # Light blue (GNOME default accent color for dark theme)
            else:
                # Use a darker accent color for light themes
                accent_color = "#3584e4"  # Blue (GNOME default accent color for light theme)

            text = f'<span foreground="{accent_color}">{text}</span>'

        cell.set_property("markup", text)
        cell.set_property("ypad", 5)

    def set_file_activated_callback(self, callback):
        """Set callback for when a file is activated."""
        self.tree_view.connect("row-activated", self._on_file_activated, callback)

    def _on_file_activated(self, tree_view, path, column, callback):
        """Handle file activation."""
        model = tree_view.get_model()
        iter = model.get_iter(path)
        file_path = model.get_value(iter, 3)  # Full path is at index 3

        # Determine file type using the get_file_type function
        file_type = get_file_type(file_path)

        callback(file_path, file_type)

    def update_file_list(self, folder_path):
        """Update the file list with files from the specified folder."""
        self.current_folder = folder_path
        self.list_store.clear()

        # Clear the playlist
        self.playlist = []

        # Update the folder title
        folder_name = os.path.basename(folder_path) or "Root"
        self.folder_title.set_markup(f"<b>{folder_name}</b>")

        # Add parent directory entry if not at root
        parent_dir = os.path.dirname(folder_path)
        if parent_dir and parent_dir != folder_path:
            # Try to load a folder-up icon
            folder_up_icon = None

            # Try different system folder-up icon names
            icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
            for icon_name in ["go-up", "folder-up", "up", "stock_up", "gtk-go-up"]:
                try:
                    icon = icon_theme.lookup_icon(icon_name, None, 32, 1, Gtk.TextDirection.NONE, 0)

                    # Try to get the pixbuf using the icon's storage type
                    if hasattr(icon, 'get_file'):
                        file = icon.get_file()
                        if file:
                            path = file.get_path()
                            if path:
                                folder_up_icon = GdkPixbuf.Pixbuf.new_from_file(path)

                    # If we couldn't get the pixbuf from the file, try other methods
                    if folder_up_icon is None and hasattr(icon, 'get_paintable'):
                        paintable = icon.get_paintable()
                        # Convert paintable to pixbuf if possible
                        # This would require additional code

                    # If we still don't have a folder_up_icon, try the old method
                    if folder_up_icon is None and hasattr(icon, 'load_icon'):
                        folder_up_icon = icon.load_icon()

                    if folder_up_icon is not None:
                        print(f"Successfully loaded up icon: {icon_name}")
                        break  # Found an icon, stop trying
                except Exception as e:
                    print(f"Failed to load up icon: {icon_name}, error: {e}")
                    continue

            # If no icon found, create a simple up arrow icon
            if folder_up_icon is None:
                folder_up_icon = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 32, 32)
                folder_up_icon.fill(0x3584E499)  # Blue color with some transparency

            # Add to list store with parent directory metadata
            self.list_store.append([folder_up_icon, "", "..", parent_dir, False, ""])

        try:
            # Collect folders and audio files separately
            folders = []
            audio_files = []

            # List all files in the current folder
            for item in os.listdir(folder_path):
                full_path = os.path.join(folder_path, item)

                # Skip hidden files
                if item.startswith('.'):
                    continue

                # Get file type
                file_type = get_file_type(full_path)

                # Collect folders
                if file_type == "Folder":
                    folders.append((item, full_path))
                # Collect audio files
                elif file_type == "Audio":
                    audio_files.append((item, full_path))

            # Sort folders alphabetically
            folders.sort(key=lambda x: x[0].lower())

            # Process folders
            for item, full_path in folders:
                # Try to load a folder icon
                folder_icon = None

                # Approach 1: Use icon theme with specific parameters
                icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())

                # Try different system folder icon names with specific parameters
                for icon_name in ["folder", "folder-symbolic", "system-file-manager", "inode-directory", "gtk-directory", "user-home"]:
                    try:
                        # Use the same parameters as in _create_default_icon which works
                        icon = icon_theme.lookup_icon(icon_name, None, 32, 1, Gtk.TextDirection.NONE, 0)

                        # In GTK 4, IconPaintable doesn't have load_icon method
                        # Initialize folder_icon for this attempt
                        icon_folder_icon = None

                        # Try to get the pixbuf using the icon's storage type
                        if hasattr(icon, 'get_file'):
                            file = icon.get_file()
                            if file:
                                path = file.get_path()
                                if path:
                                    icon_folder_icon = GdkPixbuf.Pixbuf.new_from_file(path)

                        # If we couldn't get the pixbuf from the file, try other methods
                        if icon_folder_icon is None and hasattr(icon, 'get_paintable'):
                            paintable = icon.get_paintable()
                            # Convert paintable to pixbuf if possible
                            # This would require additional code

                        # If we still don't have a folder_icon, try the old method
                        if icon_folder_icon is None and hasattr(icon, 'load_icon'):
                            icon_folder_icon = icon.load_icon()

                        # If we got an icon, use it
                        if icon_folder_icon is not None:
                            folder_icon = icon_folder_icon

                        if folder_icon is not None:
                            print(f"Successfully loaded icon: {icon_name}")
                            break  # Found an icon, stop trying
                    except Exception as e:
                        print(f"Failed to load icon: {icon_name}, error: {e}")
                        continue

                # Approach 2: Try common locations for folder icons
                if folder_icon is None:
                    common_icon_paths = [
                        "/usr/share/icons/hicolor/32x32/places/folder.png",
                        "/usr/share/icons/Adwaita/32x32/places/folder.png",
                        "/usr/share/icons/gnome/32x32/places/folder.png",
                        "/usr/share/icons/default/32x32/places/folder.png"
                    ]

                    for path in common_icon_paths:
                        if os.path.exists(path):
                            try:
                                folder_icon = GdkPixbuf.Pixbuf.new_from_file(path)
                                print(f"Successfully loaded folder icon from: {path}")
                                break
                            except Exception as e:
                                print(f"Failed to load folder icon from {path}: {e}")

                # Approach 3: Create a simple folder icon
                if folder_icon is None:
                    # Create a simple folder icon (yellow rectangle)
                    folder_icon = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 32, 32)
                    folder_icon.fill(0xFFD70099)  # Gold color with some transparency

                # Add to list store with folder metadata (empty duration for folders)
                # Use empty string for artist to not display "Folder" text
                self.list_store.append([folder_icon, "", item, full_path, False, ""])

            # Process audio files
            for item, full_path in audio_files:
                # Add audio files to playlist
                self.playlist.append(full_path)

                # Get album art
                album_art = extract_album_art(full_path)
                if album_art is None:
                    album_art = self.default_icon

                # Get metadata
                metadata = get_audio_metadata(full_path)
                artist = metadata['artist']
                title = metadata['title']

                # Get duration
                duration_seconds = get_audio_duration(full_path)
                duration_str = format_duration(duration_seconds)

                # Check if this is the currently playing file
                is_playing = (full_path == self.currently_playing)

                # Add to list store
                self.list_store.append([album_art, artist, title, full_path, is_playing, duration_str])
        except Exception as e:
            print(f"Error listing directory: {e}")

    def get_playlist(self):
        """Get the current playlist."""
        return self.playlist

    def get_track_index(self, file_path):
        """Get the index of a file in the playlist."""
        if file_path in self.playlist:
            return self.playlist.index(file_path)
        return -1

    def get_playlist_info(self, file_path):
        """Get information about the file's position in the playlist."""
        track_index = self.get_track_index(file_path)
        if track_index >= 0:
            return f"Track {track_index + 1} of {len(self.playlist)}"
        return ""

    def set_currently_playing(self, file_path):
        """Set the currently playing file and update the UI."""
        self.currently_playing = file_path

        # Update the list store to highlight the currently playing file
        for i, row in enumerate(self.list_store):
            path = row[3]  # Full path is at index 3
            row[4] = (path == file_path)  # Update is_playing flag

        # Ensure the currently playing file is visible
        if file_path:
            for i, row in enumerate(self.list_store):
                if row[3] == file_path:
                    path = Gtk.TreePath.new_from_indices([i])
                    self.tree_view.scroll_to_cell(path, None, True, 0.5, 0.5)
                    break

# This allows the file to be imported without running any code
if __name__ == "__main__":
    print("This module is not meant to be run directly.")
