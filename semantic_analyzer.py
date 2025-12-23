"""Semantic analysis for sensor configurations.

Checks:
- Pin conflicts (same pin used by multiple sensors).
- Capability validation (e.g., analog sensors on ADC-capable pins).
- Logic checks (MQTT credentials when MQTT is enabled).
"""

from typing import Any, Dict, List

from daq_config import BOARD_CATALOG, SENSOR_CATALOG


def analyze(config: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    sensors = config.get("sensors", [])
    mqtt_enabled = config.get("mqtt_enabled", True)
    wifi_ssid = config.get("wifi_ssid", "")
    wifi_password = config.get("wifi_password", "")
    mqtt_broker = config.get("mqtt_broker", "")
    board = config.get("board", "ESP32")

    board_meta = BOARD_CATALOG.get(board)
    if not board_meta:
        errors.append(f"Unsupported board: {board}")
        return errors

    adc_pins = set(board_meta.get("adc_pins", []))

    # Pin conflict and capability checks
    used_pins = {}
    for s in sensors:
        s_type = s.get("type")
        pin = s.get("pin")

        # Validate known sensor
        if s_type not in SENSOR_CATALOG:
            errors.append(f"Unsupported sensor: {s_type}")
            continue

        meta = SENSOR_CATALOG[s_type]
        requires_pin = meta.get("requires_pin", False)
        pin_capability = meta.get("pin_capability")

        if requires_pin:
            if pin is None:
                errors.append(f"Sensor {s_type} requires a pin.")
                continue

            if pin in used_pins:
                errors.append(
                    f"Pin conflict: pin {pin} already used by {used_pins[pin]}."
                )
            else:
                used_pins[pin] = s_type

            if pin_capability == "ADC" and pin not in adc_pins:
                errors.append(
                    f"Pin {pin} is not ADC-capable for board {board}; required for analog sensor {s_type}."
                )

    # Logic checks for MQTT/WiFi when enabled
    if mqtt_enabled:
        if not wifi_ssid:
            errors.append("WiFi SSID is required when MQTT is enabled.")
        if not wifi_password:
            errors.append("WiFi password is required when MQTT is enabled.")
        if not mqtt_broker:
            errors.append("MQTT broker is required when MQTT is enabled.")

    return errors

