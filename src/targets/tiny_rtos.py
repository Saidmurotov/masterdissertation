from src.ir import DAQConfigIR, HardwareResource, ResourceAssignment
from typing import Dict, Any

class TinyRTOSAdapter:
    def __init__(self, ir: DAQConfigIR):
        self.ir = ir
        self.target_model = {}

    def generate_target_model(self) -> Dict[str, Any]:
        # Map IR to a target-specific model for tiny-rtos
        self.target_model["task_name"] = "DaqTask"
        self.target_model["sample_rate"] = self.ir.sample_rate
        self.target_model["num_channels"] = len(self.ir.channels)
        self.target_model["channels"] = self.ir.channels
        
        # RTOS specific parameters
        self.target_model["rtos_task_priority"] = self.ir.target_config.get("rtos_task_priority", 5) # Default to 5
        self.target_model["rtos_stack_size"] = self.ir.target_config.get("rtos_stack_size", 256) # Default to 256 words
        self.target_model["rtos_tick_rate"] = self.ir.target_config.get("rtos_tick_rate", 1000) # Default to 1000 Hz

        # Hardware resources and assignments
        self.target_model["adcs"] = [res for res in self.ir.hardware_resources if res.resource_type == "ADC"]
        self.target_model["resource_assignments"] = self.ir.resource_assignments

        # Example of how to use allocated resources
        adc_channel_map = {}
        for assignment in self.ir.resource_assignments:
            if assignment.resource_name not in adc_channel_map:
                adc_channel_map[assignment.resource_name] = []
            adc_channel_map[assignment.resource_name].append(assignment.resource_index)
        self.target_model["adc_channel_map"] = adc_channel_map

        return self.target_model

    def generate_code(self) -> Dict[str, str]:
        # This is where Jinja2 would be used to render templates
        # For now, we return placeholder strings
        model = self.generate_target_model()
        
        main_c_content = f"""
// Generated main.c for tiny-rtos
// Task: {model['task_name']}
// Sample Rate: {model['sample_rate']} Hz
// Channels: {model['channels']}
// Priority: {model['rtos_task_priority']}
// Stack Size: {model['rtos_stack_size']} words

#include "FreeRTOS.h"
#include "task.h"
#include "hal_adc.h" // Custom HAL for ADC

void {model['task_name']}(void *pvParameters)
{{
    // Task implementation based on model
    for(;;)
    {{
        // Read ADC channels
        // ...
        vTaskDelay(pdMS_TO_TICKS(1000 / {model['sample_rate']}));
    }}
}}

void main(void)
{{
    // System init
    // ...
    xTaskCreate({model['task_name']}, "{model['task_name']}", {model['rtos_stack_size']}, NULL, {model['rtos_task_priority']}, NULL);
    vTaskStartScheduler();
}}
"""

        hal_h_content = f"""
// Generated hal_adc.h for tiny-rtos
// Defines HAL for ADC access

#ifndef HAL_ADC_H
#define HAL_ADC_H

#include <stdint.h>

void HAL_ADC_Init(void);
uint16_t HAL_ADC_ReadChannel(uint32_t adc_resource_index);

#endif // HAL_ADC_H
"""
        return {"main.c": main_c_content, "hal_adc.h": hal_h_content}

# Example usage (for testing purposes)
if __name__ == "__main__":
    ir_instance = DAQConfigIR(
        sample_rate=100,
        channels=[0, 1],
        output_file="",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4)
        ],
        resource_assignments=[
            ResourceAssignment(channel_id=0, resource_name="ADC1", resource_index=0),
            ResourceAssignment(channel_id=1, resource_name="ADC1", resource_index=1)
        ],
        target_config={
            "rtos_task_priority": 3,
            "rtos_stack_size": 512,
            "rtos_tick_rate": 1000
        }
    )
    adapter = TinyRTOSAdapter(ir_instance)
    generated_files = adapter.generate_code()
    print("--- main.c ---")
    print(generated_files["main.c"])
    print("--- hal_adc.h ---")
    print(generated_files["hal_adc.h"])
