import pytest
from src.ir import DAQConfigIR, HardwareResource, ResourceAssignment
from src.semantic_analyzer import SemanticAnalyzer
from src.generator import CodeGenerator

def test_tiny_rtos_snapshot(snapshot):
    ir = DAQConfigIR(
        sample_rate=100,
        channels=[0, 1, 2],
        output_file="",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4)
        ],
        target_config={
            "rtos_task_priority": 3,
            "rtos_stack_size": 512,
            "rtos_tick_rate": 1000,
            "microcontroller_name": "STM32F4"
        }
    )
    
    analyzer = SemanticAnalyzer()
    analyzed_ir = analyzer.analyze(ir)
    assert not analyzed_ir.semantic_errors

    generator = CodeGenerator()
    generated_files = generator.generate(analyzed_ir, "tiny-rtos")

    snapshot.snapshot_dir = 'tests/snapshots'
    snapshot.assert_match(generated_files["main.c"], 'tiny_rtos_main_c.txt')
    snapshot.assert_match(generated_files["hal_adc.h"], 'tiny_rtos_hal_h.txt')
