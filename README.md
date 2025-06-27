# Folder Audio Player

A simple folder-based audio player built with GTK4 and GStreamer.

## Features

- Browse and play audio files from folders
- Simple and intuitive user interface
- Spectrum analyzer visualization
- Shuffle playback
- MPRIS integration for system media controls
- Desktop notifications

## Requirements

- Python 3.6+
- GTK 4.0+
- GStreamer 1.0+
- PyGObject

## Installation

### From Source

1. Clone the repository:
   ```
   git clone https://github.com/ivanthecrazy/folder-audio-player.git
   cd folder-audio-player
   ```

2. Install the package:
   ```
   pip install .
   ```

   Or for development:
   ```
   pip install -e .
   ```

### Creating a Distribution Package

To create a distribution package:

1. Build the source distribution:
   ```
   python setup.py sdist
   ```

2. Build a wheel package:
   ```
   python setup.py bdist_wheel
   ```

The distribution packages will be created in the `dist` directory.

## Usage

After installation, you can launch the application from your desktop environment's application menu or by running:

```
folder-audio-player
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.