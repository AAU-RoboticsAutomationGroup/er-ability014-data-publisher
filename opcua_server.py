import asyncio
import logging
from asyncua import Server, ua
from asyncua.server.user_managers import PermissiveUserManager
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "172.20.66.174"
MQTT_TOPIC = "er/status/robot_state"
MQTT_PORT = 1883  # Default MQTT port

# Initialize MQTT client
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to MQTT broker!")
    else:
        logging.error(f"Failed to connect to MQTT broker. Return code: {rc}")

# Connect to MQTT broker
mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()  # Start MQTT client loop in a background thread

SERVER_ENDPOINT = "opc.tcp://172.20.66.174:4841/"

async def main():
    _logger = logging.getLogger(__name__)
    # Setup our server
    server = Server(user_manager=PermissiveUserManager())
    await server.init()
    server.set_endpoint(SERVER_ENDPOINT)

    # Set up our own namespace
    uri = "http://examples.freeopcua.github.io"
    idx = await server.register_namespace(uri)

    # Populating our address space
    myobj = await server.nodes.objects.add_object(idx, "ability")

    # Create the variable with String data type and default value of "1"
    robot_state = await myobj.add_variable(idx, "robot_state", "1")

    # Set the DataType attribute to String
    await robot_state.write_attribute(
        ua.AttributeIds.DataType,
        ua.DataValue(ua.Variant(ua.NodeId(ua.ObjectIds.String), ua.VariantType.NodeId))
    )

    # Set variable to be writable by clients
    await robot_state.set_writable()

    _logger.info("Starting OPCUA server!")
    async with server:
        while True:
            current_value = await robot_state.get_value()
            _logger.info("Current value: %s", current_value)

            # Publish the value to MQTT
            mqtt_client.publish(MQTT_TOPIC, str(current_value))
            _logger.info("Published value: %s", current_value)

            await asyncio.sleep(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

