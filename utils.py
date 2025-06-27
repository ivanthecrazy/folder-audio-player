import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GdkPixbuf, GLib
import io

try:
    from mutagen import File as MutagenFile
    from mutagen.id3 import ID3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

def is_audio_file(filename):
    """Check if a file is an audio file based on its extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

def get_file_type(path):
    """Determine the type of a file (Folder, Audio, or File)."""
    if os.path.isdir(path):
        return "Folder"
    elif is_audio_file(path):
        return "Audio"
    else:
        return "File"

def extract_album_art(file_path, size=32):
    """Extract album art from an audio file.

    Args:
        file_path: Path to the audio file
        size: Size to scale the image to (default: 32px)

    Returns:
        A GdkPixbuf.Pixbuf object if album art is found, None otherwise
    """
    if not MUTAGEN_AVAILABLE:
        print("Warning: mutagen library not available. Album art extraction will be disabled.")
        return None

    try:
        ext = os.path.splitext(file_path)[1].lower()

        # Handle different audio formats
        if ext == '.mp3':
            # For MP3 files
            audio = ID3(file_path)
            for tag in ['APIC:', 'APIC:Cover', 'APIC:Front Cover']:
                if tag in audio:
                    image_data = audio[tag].data
                    return _create_pixbuf_from_data(image_data, size)

        elif ext == '.flac':
            # For FLAC files
            audio = FLAC(file_path)
            if audio.pictures:
                image_data = audio.pictures[0].data
                return _create_pixbuf_from_data(image_data, size)

        elif ext == '.m4a':
            # For M4A/AAC files
            audio = MP4(file_path)
            if 'covr' in audio:
                image_data = audio['covr'][0]
                return _create_pixbuf_from_data(bytes(image_data), size)

        else:
            # For other formats, try generic approach
            audio = MutagenFile(file_path)
            if hasattr(audio, 'pictures') and audio.pictures:
                image_data = audio.pictures[0].data
                return _create_pixbuf_from_data(image_data, size)

    except Exception as e:
        print(f"Error extracting album art: {e}")

    return None

def _create_pixbuf_from_data(image_data, size=32):
    """Create a GdkPixbuf.Pixbuf from image data and resize it.

    Args:
        image_data: Raw image data
        size: Size to scale the image to (default: 32px)

    Returns:
        A GdkPixbuf.Pixbuf object scaled to the specified size
    """
    try:
        loader = GdkPixbuf.PixbufLoader()
        loader.write(image_data)
        loader.close()
        pixbuf = loader.get_pixbuf()

        # Resize the pixbuf while maintaining aspect ratio
        width = pixbuf.get_width()
        height = pixbuf.get_height()
        if width > height:
            new_width = size
            new_height = int(height * size / width)
        else:
            new_height = size
            new_width = int(width * size / height)

        scaled_pixbuf = pixbuf.scale_simple(new_width, new_height, GdkPixbuf.InterpType.BILINEAR)
        return scaled_pixbuf
    except Exception as e:
        print(f"Error creating pixbuf: {e}")
        return None

def get_audio_metadata(file_path):
    """Extract metadata from an audio file.

    Args:
        file_path: Path to the audio file

    Returns:
        A dictionary containing 'artist', 'album', and 'title' if available
    """
    metadata = {'artist': 'Unknown Artist', 'album': 'Unknown Album', 'title': os.path.basename(file_path)}

    if not MUTAGEN_AVAILABLE:
        return metadata

    try:
        ext = os.path.splitext(file_path)[1].lower()

        # Handle different audio formats
        if ext == '.mp3':
            # For MP3 files
            audio = ID3(file_path)
            if 'TPE1' in audio:  # Artist
                metadata['artist'] = str(audio['TPE1'])
            if 'TALB' in audio:  # Album
                metadata['album'] = str(audio['TALB'])
            if 'TIT2' in audio:  # Title
                metadata['title'] = str(audio['TIT2'])

        elif ext == '.flac':
            # For FLAC files
            audio = FLAC(file_path)
            if 'artist' in audio:
                metadata['artist'] = str(audio['artist'][0])
            if 'album' in audio:
                metadata['album'] = str(audio['album'][0])
            if 'title' in audio:
                metadata['title'] = str(audio['title'][0])

        elif ext == '.m4a':
            # For M4A/AAC files
            audio = MP4(file_path)
            if '©ART' in audio:
                metadata['artist'] = str(audio['©ART'][0])
            if '©alb' in audio:
                metadata['album'] = str(audio['©alb'][0])
            if '©nam' in audio:
                metadata['title'] = str(audio['©nam'][0])

        else:
            # For other formats, try generic approach
            audio = MutagenFile(file_path)
            if hasattr(audio, 'tags') and audio.tags:
                tags = audio.tags
                if 'artist' in tags:
                    metadata['artist'] = str(tags['artist'][0])
                if 'album' in tags:
                    metadata['album'] = str(tags['album'][0])
                if 'title' in tags:
                    metadata['title'] = str(tags['title'][0])

    except Exception as e:
        print(f"Error extracting metadata: {e}")

    return metadata

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds.

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds as a float, or 0 if duration cannot be determined
    """
    if not MUTAGEN_AVAILABLE:
        return 0

    try:
        # Use mutagen to get the audio file info
        audio = MutagenFile(file_path)
        if audio is None:
            return 0

        # Get duration in seconds
        if hasattr(audio, 'info') and hasattr(audio.info, 'length'):
            return audio.info.length

    except Exception as e:
        print(f"Error getting audio duration: {e}")

    return 0

def format_duration(seconds):
    """Format duration in seconds to MM:SS format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string in MM:SS format
    """
    if seconds <= 0:
        return "00:00"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def get_settings_path():
    """Get the path to the settings file.

    Returns:
        Path to the settings file
    """
    config_dir = os.path.join(GLib.get_user_config_dir(), "folder-audio-player")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "settings.ini")

def save_setting(key, value):
    """Save a setting to the settings file.

    Args:
        key: Setting key
        value: Setting value
    """
    key_file = GLib.KeyFile()
    settings_path = get_settings_path()

    # Load existing settings if the file exists
    try:
        if os.path.exists(settings_path):
            key_file.load_from_file(settings_path, GLib.KeyFileFlags.NONE)
    except Exception as e:
        print(f"Error loading settings: {e}")

    # Set the new value
    if isinstance(value, bool):
        key_file.set_boolean("Settings", key, value)
    elif isinstance(value, int):
        key_file.set_integer("Settings", key, value)
    elif isinstance(value, float):
        key_file.set_double("Settings", key, value)
    else:
        key_file.set_string("Settings", key, str(value))

    # Save the settings
    try:
        key_file.save_to_file(settings_path)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_setting(key, default_value):
    """Load a setting from the settings file.

    Args:
        key: Setting key
        default_value: Default value to return if the setting is not found

    Returns:
        The setting value, or the default value if not found
    """
    key_file = GLib.KeyFile()
    settings_path = get_settings_path()

    # Load settings if the file exists
    try:
        if os.path.exists(settings_path):
            key_file.load_from_file(settings_path, GLib.KeyFileFlags.NONE)
    except Exception as e:
        print(f"Error loading settings: {e}")
        return default_value

    # Get the value
    try:
        if isinstance(default_value, bool):
            return key_file.get_boolean("Settings", key)
        elif isinstance(default_value, int):
            return key_file.get_integer("Settings", key)
        elif isinstance(default_value, float):
            return key_file.get_double("Settings", key)
        else:
            return key_file.get_string("Settings", key)
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return default_value
