import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class AudioPlayer:
    """Audio player class that handles playback using GStreamer."""
    
    def __init__(self):
        # Initialize GStreamer if not already initialized
        if not Gst.is_initialized():
            Gst.init(None)
        
        # Create GStreamer player
        self.player = Gst.ElementFactory.make("playbin", "player")
        
        # Create a bus to get events from the player
        self.bus = self.player.get_bus()
        self.bus.add_signal_watch()
        
        # State variables
        self.current_file = None
        self.playing = False
        self.timeout_id = None
        
    def set_on_message_callback(self, callback):
        """Set callback for bus messages."""
        self.bus.connect("message", callback)
        
    def play(self, file_path):
        """Play an audio file."""
        self.current_file = file_path
        
        # Stop any current playback
        self.player.set_state(Gst.State.NULL)
        
        # Set the URI to play
        self.player.set_property("uri", f"file://{file_path}")
        
        # Start playing
        self.player.set_state(Gst.State.PLAYING)
        
        # Set playing state
        self.playing = True
        
        return True
        
    def toggle_playback(self):
        """Toggle between play and pause."""
        if not self.current_file:
            return False
            
        self.playing = not self.playing
        
        if self.playing:
            # Resume playback
            self.player.set_state(Gst.State.PLAYING)
        else:
            # Pause playback
            self.player.set_state(Gst.State.PAUSED)
            
        return True
        
    def stop(self):
        """Stop playback."""
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None
            
        self.player.set_state(Gst.State.NULL)
        self.playing = False
        self.current_file = None
        
    def seek(self, position_seconds):
        """Seek to a position in the current track."""
        if not self.current_file:
            return False
            
        # Convert seconds to nanoseconds for GStreamer
        position_ns = int(position_seconds * Gst.SECOND)
        
        # Seek to the new position
        return self.player.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            position_ns
        )
        
    def get_position(self):
        """Get the current playback position in seconds."""
        success, position = self.player.query_position(Gst.Format.TIME)
        if success:
            return position / Gst.SECOND
        return 0
        
    def get_duration(self):
        """Get the duration of the current track in seconds."""
        success, duration = self.player.query_duration(Gst.Format.TIME)
        if success:
            return duration / Gst.SECOND
        return 0
        
    def set_progress_update_callback(self, callback, interval=1000):
        """Set a callback to update progress at regular intervals."""
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            
        self.timeout_id = GLib.timeout_add(interval, callback)
        return self.timeout_id