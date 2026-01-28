class Encoder:
    """High-level rotary encoder with 0-100 clamping and colour-gradient LED."""

    def __init__(self, seesaw, name, min_val=0, max_val=100,
                 neopixel_pin=6, neopixel_count=4, brightness=0.3):
        self.seesaw = seesaw
        self.name = name
        self.min_val = min_val
        self.max_val = max_val
        self.neopixel_pin = neopixel_pin
        self.neopixel_count = neopixel_count
        self.brightness = brightness
        self._value = 0

    def begin(self):
        """Initialise NeoPixel and reset encoder position to 0."""
        self.seesaw.reset()
        self.seesaw.init_neopixel(self.neopixel_pin, self.neopixel_count)
        self.seesaw.set_encoder_position(0)
        self._value = 0
        self._update_led()

    def update(self):
        """Read encoder, clamp to range, update LED. Returns True if value changed."""
        raw = self.seesaw.get_encoder_position()
        clamped = max(self.min_val, min(self.max_val, raw))
        if clamped != raw:
            self.seesaw.set_encoder_position(clamped)
        changed = clamped != self._value
        self._value = clamped
        if changed:
            self._update_led()
        return changed

    @property
    def value(self):
        return self._value

    def _update_led(self):
        r, g, b = self._value_to_rgb(self._value)
        self.seesaw.set_all_neopixels(r, g, b, self.neopixel_count)

    def _value_to_rgb(self, val):
        """Map 0-100 to blue(0) -> green(50) -> red(100), scaled by brightness."""
        br = self.brightness
        if val <= 50:
            t = val / 50.0
            r = 0
            g = int(255 * t * br)
            b = int(255 * (1.0 - t) * br)
        else:
            t = (val - 50) / 50.0
            r = int(255 * t * br)
            g = int(255 * (1.0 - t) * br)
            b = 0
        return (r, g, b)
