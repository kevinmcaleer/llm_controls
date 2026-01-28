"""
Change the I2C address of an Adafruit QT Rotary Encoder (Seesaw).

Usage:
  1. Connect ONLY ONE encoder to the Pico W I2C bus
  2. Set NEW_ADDRESS below to the desired address
  3. Run this script
  4. Label the encoder, disconnect it, repeat for the next one

Address plan:
  Encoder 1 (humour):          0x36 (default - no change needed)
  Encoder 2 (sarcasm):         0x37
  Encoder 3 (response_length): 0x38
"""

from machine import Pin, SoftI2C
from time import sleep_ms
from seesaw import Seesaw

# ---- EDIT THIS BEFORE EACH RUN ----
NEW_ADDRESS = 0x37
# ------------------------------------

I2C_ID = 0
I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 50_000

SEESAW_DEFAULT = 0x36


def main():
    i2c = SoftI2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=I2C_FREQ)
    sleep_ms(1000)

    devices = i2c.scan()
    print("I2C scan:", [hex(d) for d in devices])

    if len(devices) == 0:
        print("ERROR: No devices found. Check wiring.")
        return

    if len(devices) > 1:
        print("ERROR: Multiple devices found. Connect only ONE encoder at a time.")
        return

    current_addr = devices[0]
    print("Found device at:", hex(current_addr))

    if current_addr == NEW_ADDRESS:
        print("Device is already at the target address", hex(NEW_ADDRESS))
        return

    ss = Seesaw(i2c, current_addr)

    # Reset device before communicating
    print("Resetting device...")
    ss.reset()

    # Verify it's a seesaw device
    hw_id = ss.get_hw_id()
    print("Seesaw HW ID:", hex(hw_id))

    # Read current EEPROM value
    eeprom_addr = ss.read_eeprom_address()
    print("EEPROM stored address:", hex(eeprom_addr))

    print("Changing address from", hex(current_addr), "to", hex(NEW_ADDRESS), "...")

    # Write new address to EEPROM
    ss.change_i2c_address(NEW_ADDRESS)

    # Verify the write
    eeprom_addr = ss.read_eeprom_address()
    print("EEPROM address after write:", hex(eeprom_addr))

    # Reset the device (still at old address until reboot completes)
    print("Resetting device...")
    ss.reset()

    # Scan again to verify
    sleep_ms(200)
    devices = i2c.scan()
    print("I2C scan after reset:", [hex(d) for d in devices])

    if NEW_ADDRESS in devices:
        print("SUCCESS: Device now at", hex(NEW_ADDRESS))
    else:
        print("WARNING: Device not found at new address.")
        print("Try power-cycling the encoder and scanning again.")


main()
