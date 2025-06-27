import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

class PlayerControls(Gtk.Box):
    """UI component for player controls."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        # Add a section title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title_box.set_margin_start(10)
        title_box.set_margin_end(10)
        title_box.set_margin_top(10)
        title_box.set_margin_bottom(5)

        header_title = Gtk.Label()
        header_title.set_markup("<b>Now Playing</b>")
        header_title.set_halign(Gtk.Align.START)
        title_box.append(header_title)

        self.append(title_box)

        # Create a box for the album art and controls
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_box.set_margin_start(10)
        content_box.set_margin_end(10)
        content_box.set_margin_top(10)
        content_box.set_margin_bottom(10)

        # Album art placeholder
        self.album_art = Gtk.Image()
        self.album_art.set_from_icon_name("audio-x-generic")
        self.album_art.set_pixel_size(128)
        content_box.append(self.album_art)

        # Song info and controls
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        info_box.set_hexpand(True)

        # Song title
        self.song_title = Gtk.Label()
        self.song_title.set_markup("<b>No song selected</b>")
        self.song_title.set_halign(Gtk.Align.START)
        info_box.append(self.song_title)

        # Artist/album info
        self.song_info = Gtk.Label(label="")
        self.song_info.set_halign(Gtk.Align.START)
        info_box.append(self.song_info)

        # Playback controls
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        controls_box.set_halign(Gtk.Align.CENTER)
        controls_box.set_margin_top(10)

        # Previous button
        self.prev_button = Gtk.Button()
        self.prev_button.set_icon_name("media-skip-backward-symbolic")
        controls_box.append(self.prev_button)

        # Play/Pause button
        self.play_button = Gtk.Button()
        self.play_button.set_icon_name("media-playback-start-symbolic")
        controls_box.append(self.play_button)

        # Next button
        self.next_button = Gtk.Button()
        self.next_button.set_icon_name("media-skip-forward-symbolic")
        controls_box.append(self.next_button)

        # Shuffle button
        self.shuffle_button = Gtk.ToggleButton()
        self.shuffle_button.set_icon_name("media-playlist-shuffle-symbolic")
        self.shuffle_button.set_tooltip_text("Shuffle")
        self.shuffle_button.set_margin_start(10)  # Add some spacing
        controls_box.append(self.shuffle_button)

        # Trash button
        self.trash_button = Gtk.Button()
        self.trash_button.set_icon_name("user-trash-symbolic")
        self.trash_button.set_tooltip_text("Delete current track")
        self.trash_button.set_margin_start(10)  # Add some spacing
        controls_box.append(self.trash_button)

        info_box.append(controls_box)

        # Progress bar
        self.progress_bar = Gtk.Scale()
        self.progress_bar.set_draw_value(False)
        self.progress_bar.set_range(0, 100)
        self.progress_bar.set_value(0)
        self.progress_bar.set_hexpand(True)
        self.progress_bar.set_margin_top(10)
        info_box.append(self.progress_bar)

        content_box.append(info_box)
        self.append(content_box)

    def set_callbacks(self, play_callback, prev_callback, next_callback, progress_callback, shuffle_callback=None, trash_callback=None):
        """Set callbacks for player control buttons."""
        self.play_button.connect("clicked", lambda button: play_callback())
        self.prev_button.connect("clicked", lambda button: prev_callback())
        self.next_button.connect("clicked", lambda button: next_callback())
        self.progress_bar.connect("change-value", lambda scale, scroll_type, value: progress_callback(value))
        if shuffle_callback:
            self.shuffle_button.connect("toggled", lambda button: shuffle_callback(button.get_active()))
        if trash_callback:
            self.trash_button.connect("clicked", lambda button: trash_callback())

    def update_play_button_state(self, is_playing):
        """Update the play/pause button icon based on playback state."""
        if is_playing:
            self.play_button.set_icon_name("media-playback-pause-symbolic")
        else:
            self.play_button.set_icon_name("media-playback-start-symbolic")

    def update_track_info(self, title, info=""):
        """Update the track information displayed."""
        if title:
            self.song_title.set_markup(f"<b>{title}</b>")
        else:
            self.song_title.set_markup("<b>No song selected</b>")

        self.song_info.set_text(info)

    def update_progress(self, position, duration):
        """Update the progress bar."""
        if duration > 0:
            self.progress_bar.set_range(0, duration)
            self.progress_bar.set_value(position)

    def update_shuffle_button_state(self, is_shuffled):
        """Update the shuffle button state.

        Args:
            is_shuffled: Boolean indicating whether shuffle is enabled.
        """
        # Set the button state
        self.shuffle_button.set_active(is_shuffled)

        # Update the button appearance
        if is_shuffled:
            self.shuffle_button.add_css_class("suggested-action")  # Highlight when active
        else:
            self.shuffle_button.remove_css_class("suggested-action")

    def update_album_art(self, pixbuf=None):
        """Update the album art image.

        Args:
            pixbuf: A GdkPixbuf.Pixbuf object containing the album art image.
                   If None, a default icon will be used.
        """
        if pixbuf:
            # Scale the pixbuf to a reasonable size while maintaining aspect ratio
            width = pixbuf.get_width()
            height = pixbuf.get_height()
            max_size = 128

            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))

            scaled_pixbuf = pixbuf.scale_simple(new_width, new_height, 2)  # 2 = GdkPixbuf.InterpType.BILINEAR
            self.album_art.set_from_pixbuf(scaled_pixbuf)
        else:
            # Use default icon if no album art is available
            self.album_art.set_from_icon_name("audio-x-generic")
            self.album_art.set_pixel_size(128)

# This allows the file to be imported without running any code
if __name__ == "__main__":
    print("This module is not meant to be run directly.")
