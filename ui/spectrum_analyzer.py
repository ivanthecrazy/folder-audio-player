import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gdk, GLib
import cairo

class SpectrumAnalyzer(Gtk.DrawingArea):
    """UI component for audio spectrum visualization."""

    def __init__(self):
        super().__init__()

        # Set a fixed height of 100px as requested
        self.set_content_height(100)
        self.set_hexpand(True)

        # Set margins
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(5)
        self.set_margin_bottom(10)

        # Initialize spectrum data
        self.spectrum_data = [0] * 64  # 64 frequency bands

        # Set up drawing
        self.set_draw_func(self._draw, None)

        # Set up a timer for animation
        self.timeout_id = None

        # Initially visible
        self.is_visible = True

    def _draw(self, area, cr, width, height, user_data):
        """Draw the spectrum visualization."""
        # Clear the background
        cr.set_source_rgba(0, 0, 0, 0.1)  # Transparent background
        cr.paint()

        # No data, just draw a line
        if all(x == 0 for x in self.spectrum_data):
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.5)  # Gray line
            cr.set_line_width(1)
            cr.move_to(0, height / 2)
            cr.line_to(width, height / 2)
            cr.stroke()
            return

        # Draw the spectrum bars
        bar_width = width / len(self.spectrum_data)
        bar_spacing = 1  # Space between bars
        effective_bar_width = bar_width - bar_spacing

        for i, magnitude in enumerate(self.spectrum_data):
            # Normalize magnitude to height
            bar_height = magnitude * height

            # Ensure minimum visible height
            if bar_height < 2 and magnitude > 0:
                bar_height = 2

            # Calculate position
            x = i * bar_width
            y = height - bar_height

            # Draw gradient bar
            gradient = cairo.LinearGradient(0, height, 0, 0)
            gradient.add_color_stop_rgba(0, 0.2, 0.6, 1.0, 0.8)  # Blue at bottom
            gradient.add_color_stop_rgba(1, 0.8, 0.3, 0.0, 0.8)  # Orange at top

            cr.set_source(gradient)
            cr.rectangle(x, y, effective_bar_width, bar_height)
            cr.fill()

    def update_spectrum(self, spectrum_data):
        """Update the spectrum data and trigger a redraw."""
        self.spectrum_data = spectrum_data
        self.queue_draw()

    def start_animation(self):
        """Start the animation if not already running."""
        if self.timeout_id is None:
            self.timeout_id = GLib.timeout_add(100, self._animate)

    def stop_animation(self):
        """Stop the animation."""
        if self.timeout_id:
            GLib.source_remove(self.timeout_id)
            self.timeout_id = None

    def _animate(self):
        """Animate the spectrum when no real data is available."""
        import random

        # Generate random spectrum data for animation
        self.spectrum_data = [random.random() * 0.8 for _ in range(64)]
        self.queue_draw()

        return True  # Keep the animation running

    def show_analyzer(self):
        """Show the spectrum analyzer by setting its height to normal."""
        if not self.is_visible:
            self.set_content_height(100)  # Restore normal height
            self.set_visible(True)
            self.is_visible = True
            self.queue_draw()

    def hide_analyzer(self):
        """Hide the spectrum analyzer by setting its height to 0."""
        if self.is_visible:
            self.set_content_height(0)  # Collapse to zero height
            self.set_visible(False)
            self.is_visible = False
            self.queue_draw()
