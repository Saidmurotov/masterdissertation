import pytest
from src.ir import DAQConfigIR, HardwareResource, ResourceAssignment
from src.semantic_analyzer import SemanticAnalyzer

def test_validate_adc_availability_success():
    ir = DAQConfigIR(
        sample_rate=100,
        channels=[0, 1, 2],
        output_file="",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4)
        ]
    )
    analyzer = SemanticAnalyzer()
    analyzer.validate_adc_availability(ir)
    assert not ir.semantic_errors

def test_validate_adc_availability_failure():
    ir = DAQConfigIR(
        sample_rate=100,
        channels=[0, 1, 2, 3, 4, 5],
        output_file="",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4)
        ]
    )
    analyzer = SemanticAnalyzer()
    analyzer.validate_adc_availability(ir)
    assert len(ir.semantic_errors) == 1
    assert "Not enough ADC capacity" in ir.semantic_errors[0]

def test_pack_channels_to_adcs():
    ir = DAQConfigIR(
        sample_rate=100,
        channels=[0, 1, 2, 3, 4, 5],
        output_file="",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4),
            HardwareResource(name="ADC2", resource_type="ADC", capacity=2)
        ]
    )
    analyzer = SemanticAnalyzer()
    analyzer.pack_channels_to_adcs(ir)
    assert len(ir.resource_assignments) == 6
    assert ir.resource_assignments[0] == ResourceAssignment(channel_id=0, resource_name="ADC1", resource_index=0)
    assert ir.resource_assignments[3] == ResourceAssignment(channel_id=3, resource_name="ADC1", resource_index=3)
    assert ir.resource_assignments[4] == ResourceAssignment(channel_id=4, resource_name="ADC2", resource_index=0)

def test_compute_adc_sampling_rate():
    ir = DAQConfigIR(
        sample_rate=1000,
        channels=[0, 1, 2, 3, 4, 5],
        output_file="",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4),
            HardwareResource(name="ADC2", resource_type="ADC", capacity=2)
        ]
    )
    analyzer = SemanticAnalyzer()
    analyzer.pack_channels_to_adcs(ir) # Need assignments first
    analyzer.compute_adc_sampling_rate(ir)
    
    adc1 = next(res for res in ir.hardware_resources if res.name == "ADC1")
    adc2 = next(res for res in ir.hardware_resources if res.name == "ADC2")

    assert "effective_sampling_rate" in adc1.properties
    assert "effective_sampling_rate" in adc2.properties
    # ADC1 handles 4 channels, ADC2 handles 2 channels
    # Total sample rate 1000 Hz, distributed to 2 ADCs -> 500 Hz per ADC
    # ADC1: 500 / 4 = 125 Hz per channel
    # ADC2: 500 / 2 = 250 Hz per channel
    assert adc1.properties["effective_sampling_rate"] == pytest.approx(125.0)
    assert adc2.properties["effective_sampling_rate"] == pytest.approx(250.0)

def test_compute_cpu_budget():
    ir = DAQConfigIR(
        sample_rate=1000,
        channels=[0, 1, 2],
        output_file="",
        hardware_resources=[]
    )
    analyzer = SemanticAnalyzer()
    analyzer.compute_cpu_budget(ir)
    assert "daq_task_cpu_time_ms" in ir.target_config
    assert "daq_task_cpu_utilization_percent" in ir.target_config
    assert ir.target_config["daq_task_cpu_utilization_percent"] == pytest.approx(80.0) # (3*0.1 + 0.5) / (1000/1000) * 100

def test_emit_schedulability_success():
    ir = DAQConfigIR(
        sample_rate=100,
        channels=[0, 1],
        output_file="",
        hardware_resources=[]
    )
    analyzer = SemanticAnalyzer()
    analyzer.compute_cpu_budget(ir) # Populate CPU utilization
    analyzer.emit_schedulability(ir)
    assert not ir.semantic_errors

def test_emit_schedulability_warning_high_cpu():
    ir = DAQConfigIR(
        sample_rate=10,
        channels=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        output_file="",
        hardware_resources=[]
    )
    analyzer = SemanticAnalyzer()
    analyzer.compute_cpu_budget(ir) # Populate CPU utilization
    analyzer.emit_schedulability(ir)
    assert len(ir.semantic_errors) == 1
    assert "very high CPU utilization" in ir.semantic_errors[0]

def test_emit_schedulability_error_unschedulable():
    ir = DAQConfigIR(
        sample_rate=10,
        channels=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        output_file="",
        hardware_resources=[]
    )
    analyzer = SemanticAnalyzer()
    analyzer.compute_cpu_budget(ir) # Populate CPU utilization
    analyzer.emit_schedulability(ir)
    assert len(ir.semantic_errors) == 2 # One from compute_cpu_budget, one from emit_schedulability
    assert "DAQ task is unschedulable" in ir.semantic_errors[1]
