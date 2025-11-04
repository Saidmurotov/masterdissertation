from daq_config import DAQConfig

def generate_nidaqmx_code(config: DAQConfig, device_name: str):
    """Generates a Python script for data acquisition using nidaqmx."""
    physical_channels = ",".join([f"{device_name}/ai{c}" for c in config.channels])

    code = f"""
// Auto-generated DAQ script for nidaqmx
// --------------------------------------
// Device: {device_name}
// Sample Rate: {config.sample_rate} Hz
// Channels: {config.channels}
// Output File: {config.output_file}
// --------------------------------------

#include <nidaqmx.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define DAQ_BUFFER_SIZE {config.sample_rate} // Read 1 second of data at a time

int main()
{{
    TaskHandle taskHandle = 0;
    float64 data[DAQ_BUFFER_SIZE * {len(config.channels)}];
    int32 read;
    char errBuff[2048] = {{0}};
    int i;

    printf("Attempting to configure task for channels: {physical_channels}\n");

    // DAQmx Configure Code
    DAQmxCreateTask("", &taskHandle);
    DAQmxCreateAIVoltageChan(taskHandle, "{physical_channels}", "", DAQmx_Val_Cfg_Default, -10.0, 10.0, DAQmx_Val_Volts, NULL);
    DAQmxCfgSampClkTiming(taskHandle, "", {config.sample_rate}, DAQmx_Val_Rising, DAQmx_Val_ContSamps, DAQ_BUFFER_SIZE);

    printf("DAQ task configured successfully. Starting data acquisition...\n");

    // DAQmx Start Code
    DAQmxStartTask(taskHandle);

    printf("Writing data to {config.output_file}. Press Ctrl+C to stop.\n");

    FILE *fp = fopen("{config.output_file}", "w");
    if (fp == NULL)
    {{
        printf("Error opening file!\n");
        return 1;
    }}

    // Write header
    fprintf(fp, "timestamp");
    for (i = 0; i < {len(config.channels)}; i++)
    {{
        fprintf(fp, ",channel_ai%d", {config.channels}[i]);
    }}
    fprintf(fp, "\n");

    while (1)
    {{
        // DAQmx Read Code
        DAQmxReadAnalogF64(taskHandle, DAQ_BUFFER_SIZE, 10.0, DAQmx_Val_GroupByScanNumber, data, DAQ_BUFFER_SIZE * {len(config.channels)}, &read, NULL);

        time_t timer;
        char buffer[26];
        struct tm* tm_info;

        time(&timer);
        tm_info = localtime(&timer);
        strftime(buffer, 26, "%Y-%m-%d %H:%M:%S", tm_info);

        fprintf(fp, "%s", buffer);
        for (i = 0; i < {len(config.channels)}; i++)
        {{
            fprintf(fp, ",%.4f", data[i]); // Assuming data is interleaved for channels
        }}
        fprintf(fp, "\n");
        printf("Saved data point at %s\n", buffer);

        // Simulate delay for next sample if needed, though DAQmxReadAnalogF64 is blocking
        // usleep(1000000 / {config.sample_rate}); // For Linux/macOS, use Sleep() for Windows
    }}

Error:
    if (DAQmxFailed(0))
        DAQmxGetExtendedErrorInfo(errBuff, 2048);
    if (taskHandle != 0)
    {{
        DAQmxStopTask(taskHandle);
        DAQmxClearTask(taskHandle);
    }}
    if (fp != NULL)
        fclose(fp);
    if (0)
        printf("DAQmx Error: %s\n", errBuff);
    return 0;
}}
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

def generate_tiny_rtos_code(config: DAQConfig, microcontroller_name: str):
    """
    Generates a C/C++ code template for a tiny-rtos task.
    This is a basic template and requires manual HAL mapping and RTOS setup.
    """
    
    # Resource allocation simulation (placeholder for actual logic)
    allocated_adc_channels = {ch: f"ADC_CHANNEL_{ch}" for ch in config.channels}
    
    code = f"""
// Auto-generated DAQ Task for {microcontroller_name} (tiny-rtos)
// ----------------------------------------------------------------
// Sample Rate: {config.sample_rate} Hz
// Channels: {config.channels}
// RTOS Task Priority: {config.rtos_task_priority}
// RTOS Stack Size: {config.rtos_stack_size} bytes
// RTOS Tick Rate: {config.rtos_tick_rate} Hz
// Output File (simulated): {config.output_file}
// ----------------------------------------------------------------

#include <stdio.h>
#include <stdint.h>
#include "FreeRTOS.h"
#include "task.h"
#include "semphr.h" // For mutex/semaphore if needed

// --- Hardware Abstraction Layer (HAL) Mappings ---
// IMPORTANT: These are placeholders. You must implement these functions
//            according to your specific microcontroller and ADC peripheral.
//            Example: STM32 HAL, ESP-IDF ADC, etc.

// Function to initialize ADC peripheral
void HAL_ADC_Init(void)
{{
    // TODO: Implement ADC initialization for your microcontroller
    // Example: MX_ADC1_Init();
    printf("HAL_ADC_Init: Initializing ADC...\n");
}}

// Function to read a specific ADC channel
// Returns the raw ADC value
uint16_t HAL_ADC_ReadChannel(uint32_t channel_id)
{{
    // TODO: Implement actual ADC read for the given channel_id
    // Example: return HAL_ADC_GetValue(&hadc1);
    // For simulation, return a dummy value
    static uint16_t simulated_adc_value[{len(config.channels)}] = {{0}};
    static int counter = 0;
    simulated_adc_value[channel_id] = (uint16_t)(2000 + 1000 * sin(counter * 0.1 + channel_id));
    counter++;
    return simulated_adc_value[channel_id];
}}

// --- DAQ Task Definition ---
#define DAQ_TASK_STACK_SIZE    {config.rtos_stack_size / 4} // FreeRTOS stack size in words
#define DAQ_TASK_PRIORITY      {config.rtos_task_priority}

// Array to store raw ADC readings
volatile uint16_t g_adc_readings[{len(config.channels)}];

// Task function for Data Acquisition
void vDaqTask(void *pvParameters)
{{
    const TickType_t xDelay = pdMS_TO_TICKS(1000 / {config.sample_rate}); // Delay in RTOS ticks
    TickType_t xLastWakeTime;
    int channel_index = 0;

    // Initialize ADC hardware
    HAL_ADC_Init();

    // Initialise the xLastWakeTime variable with the current time.
    xLastWakeTime = xTaskGetTickCount();

    printf("vDaqTask: Starting DAQ task (Priority: %d, Stack: %d words)\n", DAQ_TASK_PRIORITY, DAQ_TASK_STACK_SIZE);

    while (1)
    {{
        // Read each configured channel
        for (channel_index = 0; channel_index < {len(config.channels)}; channel_index++)
        {{
            // Map logical channel to physical ADC channel ID (example mapping)
            uint32_t physical_channel_id = {config.channels}[channel_index]; // Assuming logical channel maps directly to physical for now
            g_adc_readings[channel_index] = HAL_ADC_ReadChannel(physical_channel_id);
            printf("  Channel %d (ADC ID %d): %d\n", {config.channels}[channel_index], physical_channel_id, g_adc_readings[channel_index]);
        }}

        // TODO: Process or store g_adc_readings (e.g., send to another task via queue, write to memory)
        // For now, just print.
        printf("DAQ cycle complete. Next cycle in %d ms.\n", (1000 / {config.sample_rate}));

        // Delay until the next sampling period
        vTaskDelayUntil(&xLastWakeTime, xDelay);
    }}
}}

// --- Main function (example for RTOS setup) ---
// IMPORTANT: This main function is a placeholder. You must integrate
//            vDaqTask creation into your RTOS project's main function.

int main(void)
{{
    // TODO: Initialize your microcontroller's clock, peripherals, etc.
    // Example: HAL_Init(); SystemClock_Config();
    printf("Main: Initializing system...\n");

    // Create the DAQ task
    xTaskCreate(
        vDaqTask,                       // Pointer to the task entry function
        "DAQ_Task",                     // A descriptive name for the task
        DAQ_TASK_STACK_SIZE,            // The stack size for the task (in words)
        NULL,                           // Parameters to pass to the task
        DAQ_TASK_PRIORITY,              // The priority at which the task is created
        NULL                            // Used to pass out the created task's handle
    );

    // Start the scheduler
    printf("Main: Starting FreeRTOS scheduler...\n");
    vTaskStartScheduler();

    // Should never get here unless there is not enough RAM for the idle task
    while (1)
    {{
        // Loop forever
    }}
    return 0;
}}
"""
    return code

def generate_code(device_type: str, config: DAQConfig, **kwargs):
    """Generic code generator that calls the specific one based on device type."""
    if device_type == "NI-DAQmx":
        return generate_nidaqmx_code(config, kwargs.get("device_name"))
    elif device_type == "Serial":
        return generate_serial_code(config, kwargs.get("device_name"), kwargs.get("baud_rate"))
    elif device_type == "tiny-rtos":
        return generate_tiny_rtos_code(config, kwargs.get("microcontroller_name"))
    else:
        raise NotImplementedError(f"Code generation for {device_type} is not supported.")
