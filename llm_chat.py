#!/usr/bin/env python3
"""
CLI chat with Ollama that responds to MQTT-controlled parameters.

Encoder values (0-100) control:
  - humour: How humorous/playful the responses are
  - sarcasm: Level of sarcasm in responses
  - response_length: How verbose the responses are
"""

import json
import threading
import requests
import paho.mqtt.client as mqtt

# Configuration
MQTT_BROKER = "192.168.1.152"
MQTT_PORT = 1883
MQTT_TOPIC = "llm/controls"

OLLAMA_URL = "http://localhost:8000/api/chat"
OLLAMA_MODEL = "llama3.2:3b"

# Current encoder values (updated by MQTT)
controls = {
    "humour": 50,
    "sarcasm": 50,
    "response_length": 50,
}
controls_lock = threading.Lock()


def build_system_prompt():
    """Build a system prompt based on current encoder values."""
    with controls_lock:
        humour = controls["humour"]
        sarcasm = controls["sarcasm"]
        length = controls["response_length"]

    parts = ["You are a helpful assistant."]

    # Humour (0 = serious, 100 = very playful)
    if humour < 20:
        parts.append("Be completely serious and professional. No jokes or levity.")
    elif humour < 40:
        parts.append("Be mostly serious with occasional light moments.")
    elif humour < 60:
        parts.append("Balance helpfulness with a friendly, approachable tone.")
    elif humour < 80:
        parts.append("Be playful and include humor where appropriate.")
    else:
        parts.append("Be very playful and humorous. Include jokes and wit freely.")

    # Sarcasm (0 = earnest, 100 = very sarcastic)
    if sarcasm < 20:
        parts.append("Be completely earnest and sincere.")
    elif sarcasm < 40:
        parts.append("Be mostly sincere with rare dry wit.")
    elif sarcasm < 60:
        parts.append("Include occasional dry humor or mild sarcasm.")
    elif sarcasm < 80:
        parts.append("Be notably sarcastic and use irony frequently.")
    else:
        parts.append("Be very sarcastic. Use heavy irony and sardonic wit.")

    # Response length (0 = terse, 100 = verbose)
    if length < 20:
        parts.append("Be extremely brief. One or two sentences maximum.")
    elif length < 40:
        parts.append("Keep responses short and concise.")
    elif length < 60:
        parts.append("Use moderate length responses.")
    elif length < 80:
        parts.append("Provide detailed, thorough responses.")
    else:
        parts.append("Be very detailed and comprehensive. Elaborate fully.")

    return " ".join(parts)


def on_mqtt_connect(client, userdata, flags, rc, properties=None):
    """Called when connected to MQTT broker."""
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER}")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"[MQTT] Connection failed with code {rc}")


def on_mqtt_message(client, userdata, msg):
    """Called when an MQTT message is received."""
    try:
        payload = json.loads(msg.payload.decode())
        with controls_lock:
            for key in controls:
                if key in payload:
                    controls[key] = payload[key]
        print(f"\n[Controls updated] humour={controls['humour']}, "
              f"sarcasm={controls['sarcasm']}, length={controls['response_length']}")
        print("You: ", end="", flush=True)
    except json.JSONDecodeError:
        pass


def start_mqtt():
    """Start MQTT client in background thread."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        return client
    except Exception as e:
        print(f"[MQTT] Could not connect: {e}")
        print("[MQTT] Continuing without live updates...")
        return None


def chat(messages):
    """Send messages to Ollama and stream the response."""
    system_prompt = build_system_prompt()

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": full_messages,
                "stream": True,
            },
            stream=True,
        )
        response.raise_for_status()

        assistant_message = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "message" in data:
                    chunk = data["message"].get("content", "")
                    print(chunk, end="", flush=True)
                    assistant_message += chunk

        print()
        return assistant_message

    except requests.exceptions.ConnectionError:
        print("[Error] Cannot connect to Ollama. Is it running?")
        return None
    except Exception as e:
        print(f"[Error] {e}")
        return None


def main():
    print("LLM Chat with Physical Controls")
    print("================================")
    print(f"Model: {OLLAMA_MODEL}")
    print(f"MQTT: {MQTT_BROKER}:{MQTT_PORT} topic={MQTT_TOPIC}")
    print("Type 'quit' to exit, 'status' to see current controls\n")

    mqtt_client = start_mqtt()
    messages = []

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() == "quit":
                break

            if user_input.lower() == "status":
                with controls_lock:
                    print(f"[Status] humour={controls['humour']}, "
                          f"sarcasm={controls['sarcasm']}, "
                          f"length={controls['response_length']}")
                    print(f"[System prompt] {build_system_prompt()}")
                continue

            messages.append({"role": "user", "content": user_input})

            print("Assistant: ", end="", flush=True)
            response = chat(messages)

            if response:
                messages.append({"role": "assistant", "content": response})

    except KeyboardInterrupt:
        print("\n")

    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

    print("Goodbye!")


if __name__ == "__main__":
    main()
