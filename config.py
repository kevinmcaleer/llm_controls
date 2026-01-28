# I2C Configuration
I2C_ID = 0
I2C_SDA = 4
I2C_SCL = 5
I2C_FREQ = 50_000

# Encoder addresses and names
ENCODERS = [
    {"address": 0x36, "name": "humour"},
    {"address": 0x37, "name": "sarcasm"},
    {"address": 0x38, "name": "response_length"},
]

# Encoder value limits
ENCODER_MIN = 0
ENCODER_MAX = 100

# MQTT Configuration
MQTT_BROKER = "192.168.1.152"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "llm_controls"
MQTT_TOPIC = "llm/controls"

# Timing
DEBOUNCE_MS = 50

# NeoPixel settings (product 4991 has 4 NeoPixels in a ring)
LED_BRIGHTNESS = 0.3
NEOPIXEL_PIN = 6
NEOPIXEL_COUNT = 4
