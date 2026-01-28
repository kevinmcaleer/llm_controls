from machine import Pin, SoftI2C
from time import sleep, sleep_ms, ticks_ms, ticks_diff
import network
import json
from umqtt_simple import MQTTClient
from seesaw import Seesaw
from encoder import Encoder
from config import (
    I2C_SDA, I2C_SCL, I2C_FREQ,
    ENCODERS, ENCODER_MIN, ENCODER_MAX,
    MQTT_BROKER, MQTT_PORT, MQTT_CLIENT_ID, MQTT_TOPIC,
    DEBOUNCE_MS, LED_BRIGHTNESS, NEOPIXEL_PIN, NEOPIXEL_COUNT,
)
from secrets import WIFI_SSID, WIFI_PASSWORD


led = Pin("LED", Pin.OUT)


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    print("Connecting to WiFi", end="")
    while not wlan.isconnected():
        led.toggle()
        sleep(0.25)
        print(".", end="")
    led.on()
    print()
    print("WiFi connected:", wlan.ifconfig()[0])
    return wlan


def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT_ID, MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.connect()
    print("MQTT connected to", MQTT_BROKER)
    return client


def init_encoders(i2c):
    encoders = []
    for cfg in ENCODERS:
        ss = Seesaw(i2c, cfg["address"])
        enc = Encoder(
            ss, cfg["name"],
            min_val=ENCODER_MIN,
            max_val=ENCODER_MAX,
            neopixel_pin=NEOPIXEL_PIN,
            neopixel_count=NEOPIXEL_COUNT,
            brightness=LED_BRIGHTNESS,
        )
        enc.begin()
        print("Encoder '{}' ready at {}".format(cfg["name"], hex(cfg["address"])))
        encoders.append(enc)
    return encoders


def main():
    # Init I2C and verify all encoders are present
    i2c = SoftI2C(scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=I2C_FREQ)
    sleep_ms(100)

    devices = i2c.scan()
    print("I2C scan:", [hex(d) for d in devices])

    expected = [cfg["address"] for cfg in ENCODERS]
    missing = [hex(a) for a in expected if a not in devices]
    if missing:
        print("ERROR: Missing encoders at addresses:", missing)
        print("Run set_address.py to assign addresses first.")
        return

    encoders = init_encoders(i2c)

    # Connect network
    wlan = connect_wifi()
    mqtt = connect_mqtt()

    # Publish initial state
    payload = {enc.name: enc.value for enc in encoders}
    mqtt.publish(MQTT_TOPIC, json.dumps(payload))
    print("Initial:", payload)

    last_publish = ticks_ms()
    last_values = dict(payload)

    # Main loop
    while True:
        try:
            any_changed = False
            for enc in encoders:
                try:
                    if enc.update():
                        any_changed = True
                except OSError as e:
                    print("I2C error on '{}': {}".format(enc.name, e))

            now = ticks_ms()
            if any_changed and ticks_diff(now, last_publish) >= DEBOUNCE_MS:
                payload = {enc.name: enc.value for enc in encoders}
                if payload != last_values:
                    msg = json.dumps(payload)
                    mqtt.publish(MQTT_TOPIC, msg)
                    last_values = dict(payload)
                    last_publish = now
                    led.toggle()
                    print(msg)

            sleep_ms(10)

        except OSError as e:
            print("MQTT error:", e)
            print("Reconnecting...")
            try:
                mqtt.disconnect()
            except Exception:
                pass
            sleep(2)
            if not wlan.isconnected():
                wlan = connect_wifi()
            mqtt = connect_mqtt()


main()
