from pathlib import Path
from typing import Any, Dict, List, Optional


TEMPLATE_ROOT = Path(__file__).parent / "templates"

# Board catalog for pin capabilities and template roots
BOARD_CATALOG: Dict[str, Dict[str, Any]] = {
    "ESP32": {
        "adc_pins": {32, 33, 34, 35, 36, 39},
        "templates_root": TEMPLATE_ROOT / "esp",
    },
    "ESP8266": {
        "adc_pins": {0},  # A0
        "templates_root": TEMPLATE_ROOT / "esp",
    },
    "Arduino Uno": {
        # Arduino analog pins A0-A5 (mapped to 14-19 in many cores)
        "adc_pins": {14, 15, 16, 17, 18, 19},
        "templates_root": TEMPLATE_ROOT / "arduino",
    },
}


# Single source of truth for sensor metadata.
SENSOR_CATALOG: Dict[str, Dict[str, Any]] = {
    "DHT22": {
        "protocol": "GPIO",
        "default_pin": 4,
        "sampling_rate_hz": 1,
        "mqtt_topic": "daq/esp32_01/sensors",
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "dht22.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "dht22.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "dht22.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno"],
        "requires_pin": True,
    },
    "BMP280": {
        "protocol": "I2C",
        "default_pin": None,
        "sampling_rate_hz": 1,
        "mqtt_topic": "daq/esp32_01/sensors",
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "bmp280.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "bmp280.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "bmp280.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno"],
        "requires_pin": False,
    },
    "MQ135": {
        "protocol": "Analog",
        "default_pin": 34,
        "sampling_rate_hz": 1,
        "mqtt_topic": "daq/esp32_01/sensors",
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "mq135.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "mq135.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "mq135.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno"],
        "requires_pin": True,
        "pin_capability": "ADC",
    },
    "LDR": {
        "protocol": "Analog",
        "default_pin": 34,
        "sampling_rate_hz": 1,
        "mqtt_topic": "daq/esp32_01/sensors",
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "ldr.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "ldr.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "ldr.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno"],
        "requires_pin": True,
        "pin_capability": "ADC",
    },
}


class DAQConfig:
    def __init__(self, sample_rate, channels, output_file, rtos_task_priority=None, rtos_stack_size=None, rtos_tick_rate=None, allocated_resources=None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.output_file = output_file
        self.rtos_task_priority = rtos_task_priority
        self.rtos_stack_size = rtos_stack_size
        self.rtos_tick_rate = rtos_tick_rate
        self.allocated_resources = allocated_resources if allocated_resources is not None else {}

    def display_config(self):
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"Channels: {self.channels}")
        print(f"Output File: {self.output_file}")
        if self.rtos_task_priority is not None:
            print(f"RTOS Task Priority: {self.rtos_task_priority}")
        if self.rtos_stack_size is not None:
            print(f"RTOS Stack Size: {self.rtos_stack_size} bytes")
        if self.rtos_tick_rate is not None:
            print(f"RTOS Tick Rate: {self.rtos_tick_rate} Hz")
        if self.allocated_resources:
            print(f"Allocated Resources: {self.allocated_resources}")

    def validate_config(self):
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive.")
        if not self.channels:
            raise ValueError("Channels list cannot be empty.")
        if not self.output_file:
            raise ValueError("Output file name cannot be empty.")
        
        if self.rtos_task_priority is not None and self.rtos_task_priority <= 0:
            raise ValueError("RTOS Task Priority must be positive.")
        if self.rtos_stack_size is not None and self.rtos_stack_size <= 0:
            raise ValueError("RTOS Stack Size must be positive.")
        if self.rtos_tick_rate is not None and self.rtos_tick_rate <= 0:
            raise ValueError("RTOS Tick Rate must be positive.")

        print("Configuration is valid.")

# Example usage:
# try:
#     config = DAQConfig(sample_rate=1000, channels=[1, 2, 5], output_file="data.csv", rtos_task_priority=5, rtos_stack_size=2048, rtos_tick_rate=100)
#     config.validate_config()
#     config.display_config()
# except ValueError as e:
#     print(f"Error: {e}")
