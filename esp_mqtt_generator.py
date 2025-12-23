"""ESP MQTT code generator and simple publisher.

Uses Strategy pattern so new sensors can be added by registering metadata in
daq_config.SENSOR_CATALOG and providing a Jinja2 template.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Protocol

import paho.mqtt.client as mqtt
from jinja2 import Template

from daq_config import SENSOR_CATALOG

# MQTT defaults (can still be overridden per sensor via SENSOR_CATALOG if needed)
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "daq/esp32_01/sensors"


class UnsupportedSensorError(Exception):
    """Raised when a sensor type is not recognized."""


class IncompatibleMCUError(Exception):
    """Raised when a sensor does not support the requested MCU."""


class SensorStrategy(Protocol):
    def render(self, sensor_cfg: Dict[str, Any]) -> str:
        ...


@dataclass
class TemplateSensorStrategy:
    """Strategy that renders a Jinja2 template for a sensor."""

    template_file: Path

    def render(self, sensor_cfg: Dict[str, Any]) -> str:
        with open(self.template_file, "r", encoding="utf-8") as f:
            template = Template(f.read())
        return template.render(**sensor_cfg)


def build_strategy_registry() -> Dict[str, SensorStrategy]:
    registry: Dict[str, SensorStrategy] = {}
    for sensor_type, meta in SENSOR_CATALOG.items():
        template_path = Path(meta["template_file"])
        registry[sensor_type] = TemplateSensorStrategy(template_path)
    return registry


STRATEGIES = build_strategy_registry()


def generate_code(user_config: Dict[str, Any]) -> str:
    """Generate ESP C++ code based on user sensor selection."""
    final_code_parts: List[str] = []
    sensors = user_config.get("sensors", [])
    mcu = user_config.get("mcu", "ESP32")

    for sensor in sensors:
        s_type = sensor["type"]
        pin = sensor.get("pin")

        if s_type not in SENSOR_CATALOG:
            raise UnsupportedSensorError(f"Sensor {s_type} not supported.")

        meta = SENSOR_CATALOG[s_type]
        if mcu not in meta["mcu_support"]:
            raise IncompatibleMCUError(f"{s_type} not compatible with {mcu}")

        strategy = STRATEGIES.get(s_type)
        if not strategy:
            raise UnsupportedSensorError(f"No strategy registered for {s_type}")

        render_cfg = {"pin": pin or meta.get("default_pin")}
        final_code_parts.append(strategy.render(render_cfg))

    return "\n".join(final_code_parts)


def available_sensors() -> List[Dict[str, Any]]:
    """Expose sensor catalog for the frontend."""
    out: List[Dict[str, Any]] = []
    for sensor_type, meta in SENSOR_CATALOG.items():
        out.append(
            {
                "type": sensor_type,
                "protocol": meta.get("protocol"),
                "default_pin": meta.get("default_pin"),
                "requires_pin": meta.get("requires_pin", False),
                "sampling_rate_hz": meta.get("sampling_rate_hz"),
                "mqtt_topic": meta.get("mqtt_topic"),
                "mcu_support": meta.get("mcu_support"),
            }
        )
    return out


def publish_sensor_data(sensor_data: Dict[str, Any]) -> None:
    """Publish JSON data to MQTT broker."""
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT)
    client.publish(MQTT_TOPIC, json.dumps(sensor_data))
    client.loop()
    client.disconnect()


if __name__ == "__main__":
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

