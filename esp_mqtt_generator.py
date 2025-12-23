"""ESP MQTT code generator and simple publisher.

This module is separate from the existing NI-DAQmx/serial/tiny-RTOS generators.
It renders small C++ snippets for common sensors using Jinja2 templates and can
publish sample sensor data to an MQTT broker.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import paho.mqtt.client as mqtt
from jinja2 import Template

# MQTT defaults
MQTT_BROKER = "localhost"
# Default port for Mosquitto; adjust if you run on a different port.
MQTT_PORT = 1883
MQTT_TOPIC = "daq/esp32_01/sensors"

# Templates live under templates/esp/
TEMPLATE_ROOT = Path(__file__).parent / "templates" / "esp"


class UnsupportedSensorError(Exception):
    """Raised when a sensor type is not recognized."""


class IncompatibleMCUError(Exception):
    """Raised when a sensor does not support the requested MCU."""


SENSOR_METADATA: Dict[str, Dict[str, Any]] = {
    "DHT22": {
        "protocol": "GPIO",
        "library": "DHT.h",
        "init_code": "DHT dht({pin}, DHT22);",
        "read_code": "dht.readTemperature()",
        "mcu_support": ["ESP32", "ESP8266"],
        "template_file": TEMPLATE_ROOT / "dht22.cpp.jinja",
    },
    "BMP280": {
        "protocol": "I2C",
        "library": "Adafruit_BMP280.h",
        "init_code": "Adafruit_BMP280 bmp;",
        "read_code": "bmp.readPressure()",
        "mcu_support": ["ESP32", "ESP8266"],
        "template_file": TEMPLATE_ROOT / "bmp280.cpp.jinja",
    },
    "MQ135": {
        "protocol": "Analog",
        "library": "MQ135.h",
        "init_code": "MQ135 mq135({pin});",
        "read_code": "mq135.readGas()",
        "mcu_support": ["ESP32", "ESP8266"],
        "template_file": TEMPLATE_ROOT / "mq135.cpp.jinja",
    },
}


def generate_code(user_config: Dict[str, Any]) -> str:
    """Generate ESP C++ code based on user sensor selection."""
    final_code_parts: List[str] = []

    for sensor in user_config["sensors"]:
        s_type = sensor["type"]
        pin = sensor.get("pin", 0)

        if s_type not in SENSOR_METADATA:
            raise UnsupportedSensorError(f"Sensor {s_type} not supported.")

        if user_config["mcu"] not in SENSOR_METADATA[s_type]["mcu_support"]:
            raise IncompatibleMCUError(
                f"{s_type} not compatible with {user_config['mcu']}"
            )

        template_file: Path = SENSOR_METADATA[s_type]["template_file"]
        with open(template_file, "r", encoding="utf-8") as f:
            template = Template(f.read())
            final_code_parts.append(template.render(pin=pin))

    return "\n".join(final_code_parts)


def publish_sensor_data(sensor_data: Dict[str, Any]) -> None:
    """Publish JSON data to MQTT broker."""
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.publish(MQTT_TOPIC, json.dumps(sensor_data))
    client.loop()
    client.disconnect()


if __name__ == "__main__":
    # Example usage
    user_config = {
        "mcu": "ESP32",
        "sensors": [
            {"type": "DHT22", "pin": 4},
            {"type": "BMP280"},
            {"type": "MQ135", "pin": 34},
        ],
    }
    esp_code = generate_code(user_config)
    print("Generated ESP Code:\n", esp_code)

    sample_data = {
        "device_id": "esp32_01",
        "temperature": 25.3,
        "humidity": 60,
        "pressure": 1012,
        "gas": 350,
    }
    publish_sensor_data(sample_data)
