import json
from pathlib import Path

import pytest

import esp_mqtt_generator as gen


def test_generate_code_valid_sensors(tmp_path: Path):
    user_config = {
        "mcu": "ESP32",
        "sensors": [
            {"type": "DHT22", "pin": 4},
            {"type": "BMP280"},
            {"type": "MQ135", "pin": 34},
        ],
    }
    code = gen.generate_code(user_config)

    assert "DHT" in code
    assert "Adafruit_BMP280" in code
    assert "MQ135" in code


def test_generate_code_rejects_unsupported_sensor():
    user_config = {"mcu": "ESP32", "sensors": [{"type": "FOO"}]}
    with pytest.raises(gen.UnsupportedSensorError):
        gen.generate_code(user_config)


def test_generate_code_rejects_incompatible_mcu():
    user_config = {"mcu": "AVR", "sensors": [{"type": "DHT22", "pin": 2}]}
    with pytest.raises(gen.IncompatibleMCUError):
        gen.generate_code(user_config)


def test_publish_sensor_data(monkeypatch):
    published = {}

    class DummyClient:
        def connect(self, host, port):
            published["connect"] = (host, port)

        def publish(self, topic, payload):
            published["publish"] = (topic, json.loads(payload))

        def loop(self):
            published["loop"] = True

        def disconnect(self):
            published["disconnect"] = True

    monkeypatch.setattr(gen.mqtt, "Client", lambda: DummyClient())

    sample = {"device_id": "esp", "value": 1}
    gen.publish_sensor_data(sample)

    assert published["connect"][1] == gen.MQTT_PORT
    assert published["publish"][0] == gen.MQTT_TOPIC
    assert published["publish"][1] == sample
    assert published.get("loop")
    assert published.get("disconnect")
