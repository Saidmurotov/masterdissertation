
from daq_config import DAQConfig

def generate_nidaqmx_code(config: DAQConfig, device_name: str):
    """Generates a Python script for data acquisition using nidaqmx."""
    physical_channels = ",".join([f"{device_name}/ai{c}" for c in config.channels])

    code = f"""
# Auto-generated DAQ script for nidaqmx
# --------------------------------------
# Device: {device_name}
# Sample Rate: {config.sample_rate} Hz
# Channels: {config.channels}
# Output File: {config.output_file}
# --------------------------------------

import nidaqmx
import numpy as np
import time
import csv

# --- Configuration ---
PHYSICAL_CHANNELS = "{physical_channels}"
SAMPLE_RATE = {config.sample_rate}
SAMPLES_PER_CHANNEL = {config.sample_rate}  # Read 1 second of data at a time
OUTPUT_FILE = "{config.output_file}"

def main():
    print(f"Attempting to configure task for channels: {{PHYSICAL_CHANNELS}}")
    try:
        with nidaqmx.Task() as task:
            task.ai_channels.add_ai_voltage_chan(PHYSICAL_CHANNELS, min_val=-10.0, max_val=10.0)
            task.timing.cfg_samp_clk_timing(rate=SAMPLE_RATE, sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

            print("DAQ task configured successfully. Starting data acquisition...")
            print(f"Writing data to {{OUTPUT_FILE}}. Press Ctrl+C to stop.")

            with open(OUTPUT_FILE, 'w', newline='') as f:
                writer = csv.writer(f)
                header = ['timestamp'] + [f'channel_ai{{c}}' for c in {config.channels}]
                writer.writerow(header)

                while True:
                    data = task.read(number_of_samples_per_channel=SAMPLES_PER_CHANNEL)
                    timestamp = time.time()
                    
                    if isinstance(data, list):
                        first_samples = [channel_data[0] for channel_data in data]
                        row = [str(timestamp)] + [f"{{val:.4f}}" for val in first_samples]
                    else:
                        row = [str(timestamp), f"{{data[0]:.4f}}"]

                    writer.writerow(row)
                    print(f"Saved data point at timestamp {{timestamp}}")

    except nidaqmx.errors.DaqError as e:
        print(f"\nNI-DAQmx Error: {{e}}")
        print("Please ensure that:")
        print(f"1. A National Instruments DAQ device is connected and named '{device_name}'.")
        print("2. The NI-DAQmx drivers are installed.")
        print(f"3. The specified channels ({physical_channels}) exist on the device.")
    except KeyboardInterrupt:
        print("\nAcquisition stopped by user. Data saved to {{OUTPUT_FILE}}.")
    except Exception as e:
        print(f"An unexpected error occurred: {{e}}")

if __name__ == "__main__":
    main()

"""
    return code

def generate_serial_code(config: DAQConfig, port: str, baud_rate: int):
    """Generates a Python script for data acquisition from a serial port."""
    num_channels = len(config.channels)

    code = f"""
# Auto-generated DAQ script for Serial Port
# ------------------------------------------
# Port: {port}
# Baud Rate: {baud_rate}
# Expected Values per Line: {num_channels}
# Output File: {config.output_file}
# ------------------------------------------

import serial
import time
import csv

# --- Configuration ---
SERIAL_PORT = '{port}'
BAUD_RATE = {baud_rate}
OUTPUT_FILE = '{config.output_file}'
NUM_CHANNELS = {num_channels}

def main():
    print(f"Connecting to serial port {{SERIAL_PORT}} at {{BAUD_RATE}} baud...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2)

        print("Connection successful. Starting data acquisition...")
        print(f"Writing data to {{OUTPUT_FILE}}. Press Ctrl+C to stop.")

        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            header = ['timestamp'] + [f'value_{{i}}' for i in range(NUM_CHANNELS)]
            writer.writerow(header)

            ser.flushInput()

            while True:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    timestamp = time.time()
                    
                    print(f"Received: {{line}}")

                    try:
                        values = [float(val) for val in line.split(',')]
                        
                        if len(values) == NUM_CHANNELS:
                            writer.writerow([timestamp] + values)
                        else:
                            print(f"Warning: Expected {{NUM_CHANNELS}} values, but got {{len(values)}}.")

                    except (ValueError, TypeError):
                        print(f"Warning: Could not parse line: {{line}}")

    except serial.SerialException as e:
        print(f"\nSerial Error: {{e}}")
        print(f"Please ensure that:")
        print(f"1. The device is connected to {{SERIAL_PORT}}.")
        print(f"2. The correct drivers for the device are installed.")
        print(f"3. The port is not being used by another program.")
    except KeyboardInterrupt:
        print("\nAcquisition stopped by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {{e}}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()

"""
    return code

def generate_code(device_type: str, config: DAQConfig, **kwargs):
    """Generic code generator that calls the specific one based on device type."""
    if device_type == "NI-DAQmx":
        return generate_nidaqmx_code(config, kwargs.get("device_name"))
    elif device_type == "Serial":
        return generate_serial_code(config, kwargs.get("device_name"), kwargs.get("baud_rate"))
    else:
        raise NotImplementedError(f"Code generation for {device_type} is not supported.")
