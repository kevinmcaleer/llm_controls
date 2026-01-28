import struct
from time import sleep_ms


class Seesaw:
    """Low-level driver for Adafruit Seesaw I2C protocol (MicroPython)."""

    # Module base addresses
    STATUS_BASE = 0x00
    NEOPIXEL_BASE = 0x0E
    ENCODER_BASE = 0x11
    EEPROM_BASE = 0x0D

    # Status function registers
    STATUS_HW_ID = 0x01
    STATUS_SWRST = 0x7F

    # Encoder function registers
    ENCODER_POSITION = 0x30

    # NeoPixel function registers
    NEOPIXEL_PIN = 0x01
    NEOPIXEL_SPEED = 0x02
    NEOPIXEL_BUFLEN = 0x03
    NEOPIXEL_BUF = 0x04
    NEOPIXEL_SHOW = 0x05

    # EEPROM function registers
    EEPROM_I2C_ADDR = 0x3F

    def __init__(self, i2c, address=0x36):
        self.i2c = i2c
        self.address = address

    def _write(self, base, func, data=None, retries=3):
        """Write to a seesaw register. data is bytes/bytearray or None."""
        if data is None:
            buf = bytes([base, func])
        else:
            buf = bytes([base, func]) + bytes(data)
        for attempt in range(retries):
            try:
                self.i2c.writeto(self.address, buf)
                return
            except OSError:
                if attempt == retries - 1:
                    raise
                sleep_ms(10)

    def _read(self, base, func, nbytes, delay_ms=10, retries=3):
        """Write register address then read back nbytes after a delay."""
        for attempt in range(retries):
            try:
                self.i2c.writeto(self.address, bytes([base, func]))
                sleep_ms(delay_ms)
                return self.i2c.readfrom(self.address, nbytes)
            except OSError:
                if attempt == retries - 1:
                    raise
                sleep_ms(10)

    def reset(self):
        """Software reset the seesaw device."""
        self._write(self.STATUS_BASE, self.STATUS_SWRST, [0xFF])
        sleep_ms(500)

    def get_hw_id(self):
        """Read the hardware ID byte (should be 0x55 for SAMD09 seesaw)."""
        data = self._read(self.STATUS_BASE, self.STATUS_HW_ID, 1)
        return data[0]

    # -- Encoder --

    def get_encoder_position(self):
        """Read encoder position as a signed 32-bit integer."""
        data = self._read(self.ENCODER_BASE, self.ENCODER_POSITION, 4)
        return struct.unpack(">i", data)[0]

    def set_encoder_position(self, position):
        """Write encoder position (signed 32-bit integer)."""
        data = struct.pack(">i", position)
        self._write(self.ENCODER_BASE, self.ENCODER_POSITION, data)

    # -- NeoPixel --

    def init_neopixel(self, pin, count):
        """Initialise the NeoPixel module for `count` pixels on `pin`."""
        self._write(self.NEOPIXEL_BASE, self.NEOPIXEL_PIN, [pin])
        self._write(self.NEOPIXEL_BASE, self.NEOPIXEL_SPEED, [0x01])  # 800KHz
        buf_len = count * 3  # 3 bytes per pixel (GRB)
        self._write(
            self.NEOPIXEL_BASE,
            self.NEOPIXEL_BUFLEN,
            [(buf_len >> 8) & 0xFF, buf_len & 0xFF],
        )

    def set_all_neopixels(self, r, g, b, count):
        """Set all `count` NeoPixels to the same colour and show.

        Byte order is GRB for WS2812.
        """
        # Build: [offset_hi, offset_lo, G,R,B, G,R,B, ...]
        pixel = bytes([g, r, b])
        buf = bytes([0x00, 0x00]) + pixel * count
        self._write(self.NEOPIXEL_BASE, self.NEOPIXEL_BUF, buf)
        sleep_ms(1)
        self._write(self.NEOPIXEL_BASE, self.NEOPIXEL_SHOW)

    # -- I2C address change (for set_address.py utility) --

    def read_eeprom(self, offset):
        """Read a byte from EEPROM at the given offset."""
        data = self._read(self.EEPROM_BASE, offset, 1)
        return data[0]

    def write_eeprom(self, offset, value):
        """Write a byte to EEPROM at the given offset."""
        self._write(self.EEPROM_BASE, offset, [value])
        sleep_ms(100)

    def read_eeprom_address(self):
        """Read the I2C address stored in EEPROM."""
        return self.read_eeprom(self.EEPROM_I2C_ADDR)

    def change_i2c_address(self, new_address):
        """Write a new I2C address to the seesaw EEPROM.

        After calling this, reset the device for the change to take effect.
        """
        self._write(self.EEPROM_BASE, self.EEPROM_I2C_ADDR, [new_address])
        sleep_ms(500)
