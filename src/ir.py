from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class HardwareResource:
    name: str
    resource_type: str  # e.g., "ADC", "Timer", "GPIO"
    capacity: int = 1   # e.g., number of channels for an ADC
    properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceAssignment:
    channel_id: int
    resource_name: str
    resource_index: int # e.g., which channel on the ADC

@dataclass
class DAQConfigIR:
    # Existing fields (simplified for example)
    sample_rate: int
    channels: List[int]
    output_file: str
    
    # New fields for resource allocation
    hardware_resources: List[HardwareResource] = field(default_factory=list)
    resource_assignments: List[ResourceAssignment] = field(default_factory=list)
    
    # Placeholder for other IR elements
    target_config: Dict[str, Any] = field(default_factory=dict)
    semantic_errors: List[str] = field(default_factory=list)

# Example usage (for testing purposes)
if __name__ == "__main__":
    adc1 = HardwareResource(name="ADC1", resource_type="ADC", capacity=8, properties={"resolution_bits": 12})
    timer1 = HardwareResource(name="Timer1", resource_type="Timer", capacity=1, properties={"max_freq_hz": 10000})

    assignment1 = ResourceAssignment(channel_id=0, resource_name="ADC1", resource_index=0)
    assignment2 = ResourceAssignment(channel_id=1, resource_name="ADC1", resource_index=1)

    ir_instance = DAQConfigIR(
        sample_rate=1000,
        channels=[0, 1],
        output_file="data.csv",
        hardware_resources=[adc1, timer1],
        resource_assignments=[assignment1, assignment2]
    )

    print(ir_instance)
