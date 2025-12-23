import pytest
from fastapi.testclient import TestClient

import main_api

client = TestClient(main_api.app)


def _post(payload):
    return client.post("/generate-code", json=payload)


def test_pin_conflict():
    """
    Intellectual check: validates semantic reasoning for resource allocation.
    Two sensors on same pin should be rejected as a semantic (not syntactic) error.
    """
    resp = _post(
        {
            "mcu": "ESP32",
            "sensors": [
                {"type": "DHT22", "pin": 4},
                {"type": "LDR", "pin": 4},
            ],
            "mqtt_enabled": True,
            "wifi_ssid": "ssid",
            "wifi_password": "pass",
            "mqtt_broker": "mqtt.local",
        }
    )
    assert resp.status_code == 400
    body = resp.json()
    detail = body.get("detail", {})
    errors = detail.get("semantic_errors", [])
    assert any("conflict" in e.lower() or "already used" in e.lower() for e in errors)


def test_adc_validation():
    """
    Intellectual check: capability reasoning — analog sensor must be on ADC pin.
    """
    resp = _post(
        {
            "mcu": "ESP32",
            "sensors": [
                {"type": "LDR", "pin": 1},  # non-ADC pin
            ],
            "mqtt_enabled": True,
            "wifi_ssid": "ssid",
            "wifi_password": "pass",
            "mqtt_broker": "mqtt.local",
        }
    )
    assert resp.status_code == 400
    errors = resp.json().get("detail", {}).get("semantic_errors", [])
    assert any("adc" in e.lower() for e in errors)


def test_mqtt_credentials_required():
    """
    Intellectual check: logic validation — MQTT enabled requires WiFi credentials.
    """
    resp = _post(
        {
            "mcu": "ESP32",
            "sensors": [{"type": "DHT22", "pin": 4}],
            "mqtt_enabled": True,
            "wifi_ssid": "",
            "wifi_password": "",
            "mqtt_broker": "",
        }
    )
    assert resp.status_code == 400
    errors = resp.json().get("detail", {}).get("semantic_errors", [])
    assert any("wifi" in e.lower() or "mqtt" in e.lower() for e in errors)


def test_valid_config():
    """
    Intellectual check: positive path — valid configuration produces code.
    """
    resp = _post(
        {
            "mcu": "ESP32",
            "sensors": [
                {"type": "DHT22", "pin": 4},
                {"type": "LDR", "pin": 34},
            ],
            "mqtt_enabled": True,
            "wifi_ssid": "ssid",
            "wifi_password": "pass",
            "mqtt_broker": "mqtt.local",
        }
    )
    assert resp.status_code == 200
    code = resp.json().get("code", "")
    assert "DHT" in code or "analogRead" in code

