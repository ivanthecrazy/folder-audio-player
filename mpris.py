import gi
gi.require_version('GLib', '2.0')
from gi.repository import GLib, Gio

class MPRISInterface:
    """
    Implements the MPRIS (Media Player Remote Interfacing Specification) interface
    for exposing media player controls to the GNOME Shell and other applications.
    
    This allows playback controls to appear in the GNOME Shell's system status area
    (top bar) when clicking on the date/time.
    """
    
    # MPRIS interface names
    MPRIS_OBJECT_PATH = '/org/mpris/MediaPlayer2'
    MPRIS_INTERFACE = 'org.mpris.MediaPlayer2'
    MPRIS_PLAYER_INTERFACE = 'org.mpris.MediaPlayer2.Player'
    
    def __init__(self, app_id, app):
        """
        Initialize the MPRIS interface.
        
        Args:
            app_id: The application ID (e.g., 'dev.ivan-larionov.FolderAudioPlayer')
            app: The application instance that implements playback controls
        """
        self.app_id = app_id
        self.app = app
        self.connection = None
        self.root_interface_id = None
        self.player_interface_id = None
        
        # Initialize D-Bus connection
        self._init_dbus()
        
    def _init_dbus(self):
        """Initialize the D-Bus connection and register interfaces."""
        # Get the session bus
        self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        
        # Register the root interface
        root_xml = self._get_root_interface_xml()
        self.root_interface_id = self.connection.register_object(
            self.MPRIS_OBJECT_PATH,
            Gio.DBusNodeInfo.new_for_xml(root_xml).interfaces[0],
            self._handle_root_method_call,
            self._handle_root_get_property,
            self._handle_root_set_property
        )
        
        # Register the player interface
        player_xml = self._get_player_interface_xml()
        self.player_interface_id = self.connection.register_object(
            self.MPRIS_OBJECT_PATH,
            Gio.DBusNodeInfo.new_for_xml(player_xml).interfaces[0],
            self._handle_player_method_call,
            self._handle_player_get_property,
            self._handle_player_set_property
        )
        
        # Own the MPRIS name
        Gio.bus_own_name_on_connection(
            self.connection,
            f'org.mpris.MediaPlayer2.{self.app_id.split(".")[-1]}',
            Gio.BusNameOwnerFlags.NONE,
            None,
            None
        )
        
    def _get_root_interface_xml(self):
        """Get the XML definition for the root interface."""
        return """
        <!DOCTYPE node PUBLIC '-//freedesktop//DTD D-BUS Object Introspection 1.0//EN'
        'http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd'>
        <node>
          <interface name='org.mpris.MediaPlayer2'>
            <method name='Raise'/>
            <method name='Quit'/>
            <property name='CanQuit' type='b' access='read'/>
            <property name='CanRaise' type='b' access='read'/>
            <property name='HasTrackList' type='b' access='read'/>
            <property name='Identity' type='s' access='read'/>
            <property name='DesktopEntry' type='s' access='read'/>
            <property name='SupportedUriSchemes' type='as' access='read'/>
            <property name='SupportedMimeTypes' type='as' access='read'/>
          </interface>
        </node>
        """
        
    def _get_player_interface_xml(self):
        """Get the XML definition for the player interface."""
        return """
        <!DOCTYPE node PUBLIC '-//freedesktop//DTD D-BUS Object Introspection 1.0//EN'
        'http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd'>
        <node>
          <interface name='org.mpris.MediaPlayer2.Player'>
            <method name='Next'/>
            <method name='Previous'/>
            <method name='Pause'/>
            <method name='PlayPause'/>
            <method name='Stop'/>
            <method name='Play'/>
            <method name='Seek'>
              <arg direction='in' name='Offset' type='x'/>
            </method>
            <method name='SetPosition'>
              <arg direction='in' name='TrackId' type='o'/>
              <arg direction='in' name='Position' type='x'/>
            </method>
            <method name='OpenUri'>
              <arg direction='in' name='Uri' type='s'/>
            </method>
            <property name='PlaybackStatus' type='s' access='read'/>
            <property name='LoopStatus' type='s' access='readwrite'/>
            <property name='Rate' type='d' access='readwrite'/>
            <property name='Shuffle' type='b' access='readwrite'/>
            <property name='Metadata' type='a{sv}' access='read'/>
            <property name='Volume' type='d' access='readwrite'/>
            <property name='Position' type='x' access='read'/>
            <property name='MinimumRate' type='d' access='read'/>
            <property name='MaximumRate' type='d' access='read'/>
            <property name='CanGoNext' type='b' access='read'/>
            <property name='CanGoPrevious' type='b' access='read'/>
            <property name='CanPlay' type='b' access='read'/>
            <property name='CanPause' type='b' access='read'/>
            <property name='CanSeek' type='b' access='read'/>
            <property name='CanControl' type='b' access='read'/>
            <signal name='Seeked'>
              <arg name='Position' type='x'/>
            </signal>
          </interface>
        </node>
        """
        
    def _handle_root_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        """Handle method calls on the root interface."""
        if method_name == 'Raise':
            # Bring the application window to the front
            self.app.win.present()
            invocation.return_value(None)
        elif method_name == 'Quit':
            # Quit the application
            self.app.quit()
            invocation.return_value(None)
        else:
            invocation.return_error_literal(Gio.dbus_error_quark(), Gio.DBusError.UNKNOWN_METHOD,
                                           f"Method {method_name} not implemented")
    
    def _handle_root_get_property(self, connection, sender, object_path, interface_name, property_name):
        """Handle property get requests on the root interface."""
        if property_name == 'CanQuit':
            return GLib.Variant('b', True)
        elif property_name == 'CanRaise':
            return GLib.Variant('b', True)
        elif property_name == 'HasTrackList':
            return GLib.Variant('b', False)
        elif property_name == 'Identity':
            return GLib.Variant('s', 'Folder Audio Player')
        elif property_name == 'DesktopEntry':
            return GLib.Variant('s', self.app_id.split('.')[-1].lower())
        elif property_name == 'SupportedUriSchemes':
            return GLib.Variant('as', ['file'])
        elif property_name == 'SupportedMimeTypes':
            return GLib.Variant('as', ['audio/mpeg', 'audio/x-vorbis+ogg', 'audio/x-flac'])
        return None
    
    def _handle_root_set_property(self, connection, sender, object_path, interface_name, property_name, value):
        """Handle property set requests on the root interface."""
        # No writable properties in the root interface
        return False
    
    def _handle_player_method_call(self, connection, sender, object_path, interface_name, method_name, parameters, invocation):
        """Handle method calls on the player interface."""
        if method_name == 'Next':
            self.app.on_next_clicked()
            invocation.return_value(None)
        elif method_name == 'Previous':
            self.app.on_prev_clicked()
            invocation.return_value(None)
        elif method_name == 'Pause':
            if self.app.player.playing:
                self.app.on_play_clicked()
            invocation.return_value(None)
        elif method_name == 'PlayPause':
            self.app.on_play_clicked()
            invocation.return_value(None)
        elif method_name == 'Stop':
            self.app.player.stop()
            self.app.player_controls.update_play_button_state(False)
            self.app.update_notification()
            invocation.return_value(None)
        elif method_name == 'Play':
            if not self.app.player.playing and self.app.current_file:
                self.app.on_play_clicked()
            invocation.return_value(None)
        elif method_name == 'Seek':
            offset_us = parameters.unpack()[0]  # Microseconds
            offset_s = offset_us / 1000000.0    # Convert to seconds
            current_pos = self.app.player.get_position()
            self.app.player.seek(current_pos + offset_s)
            invocation.return_value(None)
        elif method_name == 'SetPosition':
            track_id, position_us = parameters.unpack()
            position_s = position_us / 1000000.0  # Convert to seconds
            self.app.player.seek(position_s)
            invocation.return_value(None)
        else:
            invocation.return_error_literal(Gio.dbus_error_quark(), Gio.DBusError.UNKNOWN_METHOD,
                                           f"Method {method_name} not implemented")
    
    def _handle_player_get_property(self, connection, sender, object_path, interface_name, property_name):
        """Handle property get requests on the player interface."""
        if property_name == 'PlaybackStatus':
            if not self.app.current_file:
                return GLib.Variant('s', 'Stopped')
            elif self.app.player.playing:
                return GLib.Variant('s', 'Playing')
            else:
                return GLib.Variant('s', 'Paused')
        elif property_name == 'LoopStatus':
            return GLib.Variant('s', 'None')  # We don't support looping yet
        elif property_name == 'Rate':
            return GLib.Variant('d', 1.0)
        elif property_name == 'Shuffle':
            return GLib.Variant('b', False)  # We don't support shuffle yet
        elif property_name == 'Metadata':
            return self._get_metadata_variant()
        elif property_name == 'Volume':
            return GLib.Variant('d', 1.0)  # We don't have volume control yet
        elif property_name == 'Position':
            if self.app.current_file and self.app.player:
                position_us = int(self.app.player.get_position() * 1000000)  # Convert to microseconds
                return GLib.Variant('x', position_us)
            return GLib.Variant('x', 0)
        elif property_name == 'MinimumRate':
            return GLib.Variant('d', 1.0)
        elif property_name == 'MaximumRate':
            return GLib.Variant('d', 1.0)
        elif property_name == 'CanGoNext':
            playlist = self.app.file_list.get_playlist()
            return GLib.Variant('b', playlist is not None and len(playlist) > 1)
        elif property_name == 'CanGoPrevious':
            playlist = self.app.file_list.get_playlist()
            return GLib.Variant('b', playlist is not None and len(playlist) > 1)
        elif property_name == 'CanPlay':
            return GLib.Variant('b', self.app.current_file is not None)
        elif property_name == 'CanPause':
            return GLib.Variant('b', self.app.current_file is not None)
        elif property_name == 'CanSeek':
            return GLib.Variant('b', self.app.current_file is not None)
        elif property_name == 'CanControl':
            return GLib.Variant('b', True)
        return None
    
    def _handle_player_set_property(self, connection, sender, object_path, interface_name, property_name, value):
        """Handle property set requests on the player interface."""
        # We don't support setting properties yet
        return False
    
    def _get_metadata_variant(self):
        """Get the metadata for the current track as a GLib.Variant."""
        if not self.app.current_file:
            return GLib.Variant('a{sv}', {})
        
        metadata = {}
        
        # Track ID (required)
        track_id = f'/org/mpris/MediaPlayer2/Track/{self.app.current_track_index}'
        metadata['mpris:trackid'] = GLib.Variant('o', track_id)
        
        # Track length in microseconds
        if self.app.player:
            length_us = int(self.app.player.get_duration() * 1000000)  # Convert to microseconds
            metadata['mpris:length'] = GLib.Variant('x', length_us)
        
        # Track title
        if self.app.current_track_title:
            metadata['xesam:title'] = GLib.Variant('s', self.app.current_track_title)
        
        # Album name (from folder name)
        if self.app.current_folder:
            album = self.app.current_folder.split('/')[-1]
            metadata['xesam:album'] = GLib.Variant('s', album)
        
        # URI
        if self.app.current_file:
            metadata['xesam:url'] = GLib.Variant('s', f'file://{self.app.current_file}')
        
        return GLib.Variant('a{sv}', metadata)
    
    def update_properties(self):
        """
        Update MPRIS properties when the player state changes.
        This should be called whenever the playback state, track, or position changes.
        """
        if not self.connection:
            return
            
        properties = {}
        
        # Update playback status
        if not self.app.current_file:
            properties['PlaybackStatus'] = GLib.Variant('s', 'Stopped')
        elif self.app.player.playing:
            properties['PlaybackStatus'] = GLib.Variant('s', 'Playing')
        else:
            properties['PlaybackStatus'] = GLib.Variant('s', 'Paused')
            
        # Update metadata
        properties['Metadata'] = self._get_metadata_variant()
        
        # Update can properties
        playlist = self.app.file_list.get_playlist()
        properties['CanGoNext'] = GLib.Variant('b', playlist is not None and len(playlist) > 1)
        properties['CanGoPrevious'] = GLib.Variant('b', playlist is not None and len(playlist) > 1)
        properties['CanPlay'] = GLib.Variant('b', self.app.current_file is not None)
        properties['CanPause'] = GLib.Variant('b', self.app.current_file is not None)
        properties['CanSeek'] = GLib.Variant('b', self.app.current_file is not None)
        
        # Send the PropertiesChanged signal
        self.connection.emit_signal(
            None,
            self.MPRIS_OBJECT_PATH,
            'org.freedesktop.DBus.Properties',
            'PropertiesChanged',
            GLib.Variant('(sa{sv}as)', [
                self.MPRIS_PLAYER_INTERFACE,
                properties,
                []
            ])
        )
    
    def emit_seeked(self, position):
        """
        Emit the Seeked signal.
        
        Args:
            position: Position in seconds
        """
        if not self.connection:
            return
            
        # Convert position to microseconds
        position_us = int(position * 1000000)
        
        # Emit the Seeked signal
        self.connection.emit_signal(
            None,
            self.MPRIS_OBJECT_PATH,
            self.MPRIS_PLAYER_INTERFACE,
            'Seeked',
            GLib.Variant('(x)', [position_us])
        )