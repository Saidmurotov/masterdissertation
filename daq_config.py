from pathlib import Path
from typing import Any, Dict, List, Optional


import sys
import os

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return Path(base_path) / relative_path

TEMPLATE_ROOT = get_resource_path("templates")

# Board catalog for pin capabilities and template roots
# Board catalog for pin capabilities and template roots
BOARD_CATALOG: Dict[str, Dict[str, Any]] = {
    "ESP32": {
        "platform": "espressif32",
        "board_id": "esp32dev",
        "framework": "arduino",
        "upload_protocol": "esptool",
        "adc_resolution_bits": 12,
        "pwm_capable": True,
        # GPIOs that can safely be used for ADC
        "adc_pins": {32, 33, 34, 35, 36, 39},
        "digital_pins": {2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33},
        "templates_root": TEMPLATE_ROOT / "esp",
    },
    "ESP8266": {
        "platform": "espressif8266",
        "board_id": "nodemcuv2",
        "framework": "arduino",
        "upload_protocol": "esptool",
        "adc_resolution_bits": 10,
        "pwm_capable": True,
        "adc_pins": {0},  # A0 is the only ADC
        "digital_pins": {0, 2, 4, 5, 12, 13, 14, 15, 16},
        "templates_root": TEMPLATE_ROOT / "esp8266",
    },
    "Arduino Uno": {
        "platform": "atmelavr",
        "board_id": "uno",
        "framework": "arduino",
        "upload_protocol": "arduino",
        "adc_resolution_bits": 10,
        "pwm_capable": True,
        # A0-A5 mapped as 14-19 is common in logic, but users might use A0..A5 string.
        # For simplicity here we assume digital pin numbers where A0=14.
        "adc_pins": {14, 15, 16, 17, 18, 19},
        "digital_pins": {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13},
        "templates_root": TEMPLATE_ROOT / "arduino",
    },
    "Arduino Nano": {
        "platform": "atmelavr",
        "board_id": "nanoatmega328",
        "framework": "arduino",
        "upload_protocol": "arduino",
        "adc_resolution_bits": 10,
        "pwm_capable": True,
        "adc_pins": {14, 15, 16, 17, 18, 19, 20, 21}, # A0-A7
        "digital_pins": {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13},
        "templates_root": TEMPLATE_ROOT / "arduino",
    },
    "Arduino Mega": {
        "platform": "atmelavr",
        "board_id": "megaatmega2560",
        "framework": "arduino",
        "upload_protocol": "wiring",
        "adc_resolution_bits": 10,
        "pwm_capable": True,
        # A0-A15
        "adc_pins": {54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69},
        "digital_pins": set(range(2, 54)),
        "templates_root": TEMPLATE_ROOT / "arduino",
    },
}


# Single source of truth for sensor metadata.
SENSOR_CATALOG: Dict[str, Dict[str, Any]] = {
    "DHT22": {
        "protocol": "GPIO",
        "default_pin": 4,
        "sampling_rate_hz": 0.5,
        "mqtt_topic": "daq/sensors/dht22",
        "lib_deps": ["adafruit/DHT sensor library", "adafruit/Adafruit Unified Sensor"],
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "dht22.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "dht22.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "dht22.cpp.jinja",
            "Arduino Nano": TEMPLATE_ROOT / "arduino" / "dht22.cpp.jinja",
            "Arduino Mega": TEMPLATE_ROOT / "arduino" / "dht22.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno", "Arduino Nano", "Arduino Mega"],
        "requires_pin": True,
    },
    "BMP280": {
        "protocol": "I2C",
        "default_pin": None, # I2C uses fixed pins usually
        "sampling_rate_hz": 1,
        "mqtt_topic": "daq/sensors/bmp280",
        "lib_deps": ["adafruit/Adafruit BMP280 Library", "adafruit/Adafruit Unified Sensor"],
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "bmp280.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "bmp280.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "bmp280.cpp.jinja",
            "Arduino Nano": TEMPLATE_ROOT / "arduino" / "bmp280.cpp.jinja",
            "Arduino Mega": TEMPLATE_ROOT / "arduino" / "bmp280.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno", "Arduino Nano", "Arduino Mega"],
        "requires_pin": False,
    },
    "MQ135": {
        "protocol": "Analog",
        "default_pin": 34,
        "sampling_rate_hz": 1,
        "mqtt_topic": "daq/sensors/mq135",
        "lib_deps": [], # Analog read often needs no lib, or specific MQ lib
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "mq135.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "mq135.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "mq135.cpp.jinja",
            "Arduino Nano": TEMPLATE_ROOT / "arduino" / "mq135.cpp.jinja",
            "Arduino Mega": TEMPLATE_ROOT / "arduino" / "mq135.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno", "Arduino Nano", "Arduino Mega"],
        "requires_pin": True,
        "pin_capability": "ADC",
    },
    "LDR": {
        "protocol": "Analog",
        "default_pin": 34,
        "sampling_rate_hz": 5,
        "mqtt_topic": "daq/sensors/ldr",
        "lib_deps": [],
        "templates": {
            "ESP32": TEMPLATE_ROOT / "esp" / "ldr.cpp.jinja",
            "ESP8266": TEMPLATE_ROOT / "esp" / "ldr.cpp.jinja",
            "Arduino Uno": TEMPLATE_ROOT / "arduino" / "ldr.cpp.jinja",
            "Arduino Nano": TEMPLATE_ROOT / "arduino" / "ldr.cpp.jinja",
            "Arduino Mega": TEMPLATE_ROOT / "arduino" / "ldr.cpp.jinja",
        },
        "mcu_support": ["ESP32", "ESP8266", "Arduino Uno", "Arduino Nano", "Arduino Mega"],
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
