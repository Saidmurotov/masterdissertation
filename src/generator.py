from src.ir import DAQConfigIR
from src.targets.tiny_rtos import TinyRTOSAdapter
from typing import Dict, Any

class CodeGenerator:
    def __init__(self):
        self.adapters = {
            "tiny-rtos": TinyRTOSAdapter,
            # Add other target adapters here
        }

    def generate(self, ir: DAQConfigIR, target: str) -> Dict[str, str]:
        if target not in self.adapters:
            raise ValueError(f"Unsupported target: {target}")
        
        adapter_class = self.adapters[target]
        adapter = adapter_class(ir)
        return adapter.generate_code()

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
    generator = CodeGenerator()
    generated_files = generator.generate(ir_instance, "tiny-rtos")
    print("--- Generated Code for tiny-rtos ---")
    for filename, content in generated_files.items():
        print(f"File: {filename}\n{{content}}\n")
