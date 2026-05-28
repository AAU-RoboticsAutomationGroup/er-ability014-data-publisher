import paho.mqtt.client as mqtt
import re
import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# MQTT Broker settings
MQTT_BROKER = "172.20.66.174"
MQTT_PORT = 1883
MQTT_KEEPALIVE = 60

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT broker")
    else:
        logger.error(f"Connection failed with code {rc}")

def publish_fields(client, state, states, battery, program_name):
    """Publish extracted fields as raw values to MQTT topics."""
    topics_and_payloads = [
        ("er/status/state", str(state)),
        ("er/status/state_1", states[0]),
        ("er/status/state_2", states[1]),
        ("er/status/state_3", states[2]),
        ("er/status/battery", str(battery)),
        ("er/status/program_name", program_name),
    ]

    for topic, payload in topics_and_payloads:
        client.publish(topic, payload=payload)
        logger.debug(f"Published to {topic}: {payload}")

def extract_fields(buffer):
    """Extract and validate fields from the input buffer."""
    state_match = re.search(r"state:\s*(-\d+|\d+)", buffer)
    state_text_match = re.search(r'state_text:\s*"(.*?)"', buffer)
    battery_match = re.search(r"battery:\s*(\d+\.\d+)", buffer)
    program_name_match = re.search(r'program_name:\s*"(.*?)"', buffer)

    if not all([state_match, state_text_match, battery_match, program_name_match]):
        return None

    try:
        state = int(state_match.group(1))
        state_text = state_text_match.group(1)
        battery = float(battery_match.group(1))
        program_name = program_name_match.group(1)
    except (ValueError, AttributeError) as e:
        logger.error(f"Failed to parse fields: {e}")
        return None

    # Split state_text into 3 parts, padding with empty strings if necessary
    states = [s.strip() for s in state_text.split(",")]
    states += [""] * (3 - len(states))  # Pad to 3 elements

    return state, states, battery, program_name

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE)
    client.loop_start()

    buffer = ""
    for line in sys.stdin:
        buffer += line.strip() + " "

        fields = extract_fields(buffer)
        if fields:
            state, states, battery, program_name = fields
            publish_fields(client, state, states, battery, program_name)
            logger.info(
                f"Published: state={state}, states={states}, "
                f"battery={battery}, program={program_name}"
            )
            buffer = ""  # Reset buffer
        else:
            logger.debug(f"Buffer: '{buffer}'")

if __name__ == "__main__":
    main()
