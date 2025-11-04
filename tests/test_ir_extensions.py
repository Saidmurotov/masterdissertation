import pytest
from src.ir import HardwareResource, ResourceAssignment, DAQConfigIR

def test_hardware_resource_init():
    adc = HardwareResource(name="ADC1", resource_type="ADC", capacity=8, properties={"resolution_bits": 12})
    assert adc.name == "ADC1"
    assert adc.resource_type == "ADC"
    assert adc.capacity == 8
    assert adc.properties == {"resolution_bits": 12}

    timer = HardwareResource(name="Timer1", resource_type="Timer")
    assert timer.name == "Timer1"
    assert timer.resource_type == "Timer"
    assert timer.capacity == 1 # Default capacity
    assert timer.properties == {} # Default empty dict

def test_resource_assignment_init():
    assignment = ResourceAssignment(channel_id=0, resource_name="ADC1", resource_index=0)
    assert assignment.channel_id == 0
    assert assignment.resource_name == "ADC1"
    assert assignment.resource_index == 0

def test_daq_config_ir_init_with_new_fields():
    adc = HardwareResource(name="ADC1", resource_type="ADC", capacity=8)
    assignment = ResourceAssignment(channel_id=0, resource_name="ADC1", resource_index=0)

    ir_instance = DAQConfigIR(
        sample_rate=1000,
        channels=[0, 1],
        output_file="data.csv",
        hardware_resources=[adc],
        resource_assignments=[assignment],
        target_config={"platform": "tiny-rtos"}
    )

    assert ir_instance.sample_rate == 1000
    assert ir_instance.channels == [0, 1]
    assert ir_instance.hardware_resources == [adc]
    assert ir_instance.resource_assignments == [assignment]
    assert ir_instance.target_config == {"platform": "tiny-rtos"}
    assert ir_instance.semantic_errors == []

def test_daq_config_ir_init_defaults():
    ir_instance = DAQConfigIR(
        sample_rate=500,
        channels=[0],
        output_file="sensor.log"
    )
    assert ir_instance.hardware_resources == []
    assert ir_instance.resource_assignments == []
    assert ir_instance.target_config == {}
    assert ir_instance.semantic_errors == []
