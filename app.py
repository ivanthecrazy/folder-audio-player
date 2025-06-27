import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, Adw, GLib, Gio, Gst, GdkPixbuf

from player import AudioPlayer
from ui.player_controls import PlayerControls
from ui.file_list import FileList
from ui.spectrum_analyzer import SpectrumAnalyzer
from utils import extract_album_art, save_setting, load_setting
from mpris import MPRISInterface

class FolderAudioPlayerApp(Adw.Application):
    """Main application class for the Folder Audio Player."""

    def __init__(self):
        super().__init__(application_id="dev.ivan-larionov.FolderAudioPlayer",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

        # Initialize GStreamer
        if not Gst.is_initialized():
            Gst.init(None)

        self.connect("activate", self.on_activate)

        # Initialize state variables
        # Use GNOME music folder as default, fallback to home directory if not available
        music_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC)
        if music_dir and os.path.exists(music_dir):
            self.current_folder = music_dir
        else:
            self.current_folder = GLib.get_home_dir()
        self.current_file = None
        self.current_track_index = -1
        self.current_track_title = "No song selected"
        self.current_track_info = ""
        self.current_album_art = None

        # Shuffle state
        self.shuffle_enabled = False
        self.shuffle_indices = []  # Shuffled indices for playlist

        # Spectrum analyzer state
        self.spectrum_enabled = load_setting("spectrum_enabled", True)

        # Create the audio player
        self.player = AudioPlayer()
        self.player.set_on_message_callback(self.on_player_message)

        # Initialize MPRIS interface
        self.mpris = MPRISInterface(self.get_application_id(), self)

        # Set up notification actions
        self.create_notification_actions()

    def on_activate(self, app):
        # Create the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(900, 600)
        self.win.set_title("Folder Audio Player")

        # Create a vertical box for the main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # Add a single header bar at the top
        header = Adw.HeaderBar()
        header.set_title_widget(Gtk.Label(label="Folder Audio Player"))

        # Add spectrum toggle button to the header bar
        self.spectrum_toggle_button = Gtk.ToggleButton()
        self.spectrum_toggle_button.set_icon_name("view-grid-symbolic")
        self.spectrum_toggle_button.set_tooltip_text("Toggle Spectrum Analyzer")
        self.spectrum_toggle_button.connect("toggled", self.on_spectrum_toggle)
        header.pack_end(self.spectrum_toggle_button)

        main_box.append(header)

        # Create the content area
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)

        # Top row: Now playing with controls
        self.player_controls = PlayerControls()
        self.player_controls.set_callbacks(
            play_callback=self.on_play_clicked,
            prev_callback=self.on_prev_clicked,
            next_callback=self.on_next_clicked,
            progress_callback=self.on_progress_changed,
            shuffle_callback=self.on_shuffle_toggled,
            trash_callback=self.on_trash_clicked
        )
        self.player_controls.set_vexpand(False)

        # Spectrum analyzer
        self.spectrum_analyzer = SpectrumAnalyzer()
        # Initially hide the analyzer since nothing is playing
        self.spectrum_analyzer.hide_analyzer()

        # Set the initial state of the spectrum toggle button
        self.spectrum_toggle_button.set_active(self.spectrum_enabled)

        # Set the initial appearance of the spectrum toggle button
        if self.spectrum_enabled:
            self.spectrum_toggle_button.add_css_class("suggested-action")  # Highlight when active

        # Bottom row: File list
        self.file_list = FileList()
        self.file_list.set_file_activated_callback(self.on_file_activated)
        self.file_list.set_vexpand(True)

        # Add components to the content box
        content_box.append(self.player_controls)
        content_box.append(self.spectrum_analyzer)
        content_box.append(self.file_list)

        main_box.append(content_box)

        self.win.set_content(main_box)
        self.win.present()

        # Initialize the file list with the current folder
        self.file_list.update_file_list(self.current_folder)


    def on_file_activated(self, file_path, file_type):
        """Handle file activation."""
        if file_type == "Folder":
            self.current_folder = file_path
            self.file_list.update_file_list(file_path)
        elif file_type == "Audio":
            self.play_audio_file(file_path)

    def play_audio_file(self, file_path):
        """Play an audio file."""
        self.current_file = file_path
        file_name = os.path.basename(file_path)

        # Find the index of this file in the playlist
        self.current_track_index = self.file_list.get_track_index(file_path)

        # If shuffle is enabled, regenerate the shuffle indices to include this track
        if self.shuffle_enabled and self.current_track_index >= 0:
            self._generate_shuffle_indices()

        # Update the UI
        folder_name = os.path.basename(self.current_folder)
        track_info = f"From: {folder_name}"
        playlist_info = self.file_list.get_playlist_info(file_path)
        if playlist_info:
            track_info += f" | {playlist_info}"

        # Update track info state variables
        self.current_track_title = file_name
        self.current_track_info = track_info

        self.player_controls.update_track_info(file_name, track_info)

        # Extract and display album art if available
        album_art = extract_album_art(file_path, 128)  # Use higher resolution for player controls
        self.current_album_art = album_art
        self.player_controls.update_album_art(album_art)

        # Update the file list to highlight the currently playing file
        self.file_list.set_currently_playing(file_path)

        # Start playing
        self.player.play(file_path)
        self.player_controls.update_play_button_state(True)

        # Start updating the progress bar
        self.player.set_progress_update_callback(self.update_progress)

        # Show and start the spectrum analyzer animation if enabled
        if self.spectrum_enabled:
            self.spectrum_analyzer.show_analyzer()
            self.spectrum_analyzer.start_animation()

        # Update notification
        self.update_notification()

        # Update MPRIS properties
        self.mpris.update_properties()

        print(f"Playing: {file_path} ({playlist_info})")

    def update_progress(self):
        """Update the progress bar."""
        if not self.player.playing:
            return True

        position = self.player.get_position()
        duration = self.player.get_duration()

        if duration > 0:
            self.player_controls.update_progress(position, duration)

        return True

    def on_player_message(self, bus, message):
        """Handle messages from the GStreamer bus."""
        t = message.type

        if t == Gst.MessageType.ERROR:
            self.player.stop()
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            self.player_controls.update_play_button_state(False)
            # Stop spectrum analyzer animation and hide it
            self.spectrum_analyzer.stop_animation()
            self.spectrum_analyzer.hide_analyzer()
            # Update notification to reflect stopped state
            self.update_notification()

            # Update MPRIS properties
            self.mpris.update_properties()

        elif t == Gst.MessageType.EOS:
            # End of stream, play the next track
            print("End of stream, playing next track")
            # Reset the current player state
            self.player.stop()
            self.player_controls.update_play_button_state(False)
            # Stop spectrum analyzer animation temporarily
            self.spectrum_analyzer.stop_animation()

            # Play the next track if there's a playlist
            playlist = self.file_list.get_playlist()
            if playlist and len(playlist) > 0:
                # Use the same logic as on_next_clicked
                self.on_next_clicked()
            else:
                # If no next track, hide the analyzer and update notification
                self.spectrum_analyzer.stop_animation()
                self.spectrum_analyzer.hide_analyzer()
                self.update_notification()

                # Update MPRIS properties
                self.mpris.update_properties()

    def on_play_clicked(self):
        """Handle play/pause button click."""
        if self.current_file:
            result = self.player.toggle_playback()
            if result:
                self.player_controls.update_play_button_state(self.player.playing)

                if self.player.playing:
                    print(f"Resuming: {self.current_file}")
                    # Restart progress updates if needed
                    self.player.set_progress_update_callback(self.update_progress)
                    # Show and start spectrum analyzer animation if enabled
                    if self.spectrum_enabled:
                        self.spectrum_analyzer.show_analyzer()
                        self.spectrum_analyzer.start_animation()
                else:
                    print(f"Paused: {self.current_file}")
                    # Stop spectrum analyzer animation and hide it
                    self.spectrum_analyzer.stop_animation()
                    self.spectrum_analyzer.hide_analyzer()

                # Update notification with new playback state
                self.update_notification()

                # Update MPRIS properties
                self.mpris.update_properties()

    def on_prev_clicked(self):
        """Play the previous track in the playlist."""
        playlist = self.file_list.get_playlist()
        if not playlist:
            return

        if self.shuffle_enabled and self.shuffle_indices:
            # Find the current position in the shuffle order
            try:
                current_pos = self.shuffle_indices.index(self.current_track_index)
                if current_pos > 0:
                    # Go to previous track in shuffle order
                    prev_index = self.shuffle_indices[current_pos - 1]
                else:
                    # Wrap around to the last track in shuffle order
                    prev_index = self.shuffle_indices[-1]
                self.current_track_index = prev_index
                self.play_audio_file(playlist[prev_index])
            except ValueError:
                # Current track not in shuffle order, regenerate shuffle indices
                self._generate_shuffle_indices()
                if self.shuffle_indices:
                    self.current_track_index = self.shuffle_indices[0]
                    self.play_audio_file(playlist[self.current_track_index])
        else:
            # Normal sequential playback
            if self.current_track_index > 0:
                # Go to previous track
                self.current_track_index -= 1
                self.play_audio_file(playlist[self.current_track_index])
            else:
                # Wrap around to the last track
                self.current_track_index = len(playlist) - 1
                self.play_audio_file(playlist[self.current_track_index])

        print(f"Playing previous track: {self.current_track_index + 1} of {len(playlist)}")

    def on_next_clicked(self):
        """Play the next track in the playlist."""
        playlist = self.file_list.get_playlist()
        if not playlist:
            return

        if self.shuffle_enabled and self.shuffle_indices:
            # Find the current position in the shuffle order
            try:
                current_pos = self.shuffle_indices.index(self.current_track_index)
                if current_pos < len(self.shuffle_indices) - 1:
                    # Go to next track in shuffle order
                    next_index = self.shuffle_indices[current_pos + 1]
                else:
                    # Wrap around to the first track in shuffle order
                    next_index = self.shuffle_indices[0]
                self.current_track_index = next_index
                self.play_audio_file(playlist[next_index])
            except ValueError:
                # Current track not in shuffle order, regenerate shuffle indices
                self._generate_shuffle_indices()
                if self.shuffle_indices:
                    self.current_track_index = self.shuffle_indices[0]
                    self.play_audio_file(playlist[self.current_track_index])
        else:
            # Normal sequential playback
            if self.current_track_index < len(playlist) - 1:
                # Go to next track
                self.current_track_index += 1
                self.play_audio_file(playlist[self.current_track_index])
            else:
                # Wrap around to the first track
                self.current_track_index = 0
                self.play_audio_file(playlist[self.current_track_index])

        print(f"Playing next track: {self.current_track_index + 1} of {len(playlist)}")

    def on_progress_changed(self, value):
        """Handle progress bar change to seek in the audio file."""
        if not self.player.playing or not self.current_file:
            return False

        # Seek to the new position
        self.player.seek(value)

        # Emit the Seeked signal for MPRIS
        self.mpris.emit_seeked(value)

        print(f"Seeking to {value:.2f} seconds")
        return True

    def on_shuffle_toggled(self, is_shuffled):
        """Handle shuffle button toggle."""
        self.shuffle_enabled = is_shuffled

        # Update the UI
        self.player_controls.update_shuffle_button_state(is_shuffled)

        # Generate shuffled playlist if enabled
        if is_shuffled:
            self._generate_shuffle_indices()
            print("Shuffle enabled")
        else:
            self.shuffle_indices = []
            print("Shuffle disabled")

    def on_trash_clicked(self):
        """Handle trash button click to delete the currently playing file."""
        if not self.current_file:
            return

        # Get the file name for the confirmation message
        file_name = os.path.basename(self.current_file)

        # Create a confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.win,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Delete File",
            secondary_text=f"Are you sure you want to delete '{file_name}'? This action cannot be undone."
        )

        # Connect the response signal
        dialog.connect("response", self._on_delete_dialog_response)

        # Show the dialog
        dialog.show()

    def _on_delete_dialog_response(self, dialog, response_id):
        """Handle the response from the delete confirmation dialog."""
        # Close the dialog
        dialog.destroy()

        # If the user confirmed the deletion
        if response_id == Gtk.ResponseType.OK:
            self._delete_current_file()

    def _delete_current_file(self):
        """Delete the currently playing file and play the next track."""
        if not self.current_file or not os.path.exists(self.current_file):
            return

        # Get the current playlist and track index
        playlist = self.file_list.get_playlist()
        current_index = self.current_track_index

        # Stop playback
        self.player.stop()
        # Stop spectrum analyzer animation and hide it
        self.spectrum_analyzer.stop_animation()
        self.spectrum_analyzer.hide_analyzer()

        # Get the next track to play after deletion
        next_track = None
        if playlist and len(playlist) > 1:  # If there are other tracks in the playlist
            if self.shuffle_enabled and self.shuffle_indices:
                # Find the current position in the shuffle order
                try:
                    current_pos = self.shuffle_indices.index(current_index)
                    if current_pos < len(self.shuffle_indices) - 1:
                        # Get next track in shuffle order
                        next_index = self.shuffle_indices[current_pos + 1]
                    else:
                        # Wrap around to the first track in shuffle order
                        next_index = self.shuffle_indices[0]
                    next_track = playlist[next_index]
                except ValueError:
                    # Current track not in shuffle order, use sequential next
                    if current_index < len(playlist) - 1:
                        next_track = playlist[current_index + 1]
                    else:
                        next_track = playlist[0]
            else:
                # Normal sequential playback
                if current_index < len(playlist) - 1:
                    next_track = playlist[current_index + 1]
                else:
                    next_track = playlist[0]

        # Try to delete the file
        try:
            os.remove(self.current_file)
            print(f"Deleted file: {self.current_file}")

            # Update the file list to reflect the deletion
            self.file_list.update_file_list(self.current_folder)

            # Play the next track if available
            if next_track and os.path.exists(next_track):
                self.play_audio_file(next_track)
            else:
                # Reset UI if no next track
                self.current_file = None
                self.current_track_index = -1
                self.current_track_title = "No song selected"
                self.current_track_info = ""
                self.player_controls.update_track_info("", "")
                self.player_controls.update_play_button_state(False)
                self.player_controls.update_album_art(None)

                # Update notification
                self.update_notification()

                # Update MPRIS properties
                self.mpris.update_properties()
        except Exception as e:
            # Show error dialog if deletion fails
            error_dialog = Gtk.MessageDialog(
                transient_for=self.win,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error Deleting File",
                secondary_text=f"Could not delete '{os.path.basename(self.current_file)}': {str(e)}"
            )
            error_dialog.connect("response", lambda dialog, response_id: dialog.destroy())
            error_dialog.show()
            print(f"Error deleting file: {e}")

    def _generate_shuffle_indices(self):
        """Generate a shuffled list of indices for the playlist."""
        import random

        playlist = self.file_list.get_playlist()
        if not playlist:
            return

        # Create a list of indices
        indices = list(range(len(playlist)))

        # Shuffle the indices
        random.shuffle(indices)

        # If we're currently playing a track, make sure it's first in the shuffle order
        if self.current_track_index >= 0 and self.current_track_index < len(indices):
            # Find where the current track is in the shuffled list
            current_pos = indices.index(self.current_track_index)
            # Swap it with the first position
            indices[0], indices[current_pos] = indices[current_pos], indices[0]

        self.shuffle_indices = indices
        print(f"Shuffled playlist: {self.shuffle_indices}")

    def create_notification_actions(self):
        """Set up notification actions."""
        # Add action for play/pause
        play_action = Gio.SimpleAction.new("play-pause", None)
        play_action.connect("activate", lambda action, param: self.on_play_clicked())
        self.add_action(play_action)

        # Add action for previous track
        prev_action = Gio.SimpleAction.new("previous-track", None)
        prev_action.connect("activate", lambda action, param: self.on_prev_clicked())
        self.add_action(prev_action)

        # Add action for next track
        next_action = Gio.SimpleAction.new("next-track", None)
        next_action.connect("activate", lambda action, param: self.on_next_clicked())
        self.add_action(next_action)

    def on_spectrum_toggle(self, button):
        """Handle spectrum analyzer toggle button click."""
        self.spectrum_enabled = button.get_active()

        # Save the setting
        save_setting("spectrum_enabled", self.spectrum_enabled)

        # Update the button appearance
        if self.spectrum_enabled:
            button.add_css_class("suggested-action")  # Highlight when active
        else:
            button.remove_css_class("suggested-action")

        # If music is playing, show/hide the analyzer based on the toggle state
        if self.player.playing:
            if self.spectrum_enabled:
                self.spectrum_analyzer.show_analyzer()
                self.spectrum_analyzer.start_animation()
            else:
                self.spectrum_analyzer.stop_animation()
                self.spectrum_analyzer.hide_analyzer()

        print(f"Spectrum analyzer {'enabled' if self.spectrum_enabled else 'disabled'}")

    def update_notification(self):
        """Update the notification with current track information and controls."""
        if not self.current_file:
            return

        # Create a new notification
        notification = Gio.Notification.new(self.current_track_title)
        notification.set_body(self.current_track_info)

        # Set notification priority to high to ensure it appears in notification center
        notification.set_priority(Gio.NotificationPriority.HIGH)

        # Set notification category to "x-gnome.music" for media players
        notification.set_category("x-gnome.music")

        # Note: We want the notification to be resident, but set_hint is not available
        # in Gio.Notification. The HIGH priority and x-gnome.music category should
        # help ensure the notification appears in the notification center.

        # Add playback control actions
        notification.add_button("Previous", "app.previous-track")

        # Change button text based on playback state
        if self.player.playing:
            notification.add_button("Pause", "app.play-pause")
        else:
            notification.add_button("Play", "app.play-pause")

        notification.add_button("Next", "app.next-track")

        # Set notification icon from album art if available
        if self.current_album_art:
            # We need to save the album art to a temporary file to use it as an icon
            # This is a limitation of Gio.Notification
            # For simplicity, we'll use the default icon for now
            pass

        # Set default notification icon if no album art
        notification.set_icon(Gio.ThemedIcon.new("audio-x-generic"))

        # Send the notification with a unique ID based on the track to avoid overwriting
        notification_id = f"now-playing-{self.current_track_index}"
        self.send_notification(notification_id, notification)
