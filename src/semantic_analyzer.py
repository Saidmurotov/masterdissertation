from src.ir import DAQConfigIR, HardwareResource, ResourceAssignment
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import math

@dataclass
class Diagnostic:
    severity: str  # e.g., "ERROR", "WARNING", "INFO"
    message: str
    rule_id: str
    suggestion: Optional[str] = None
    location: Optional[str] = None  # e.g., "file:line_number"

class SemanticAnalyzer:
    def __init__(self):
        self.phases = [
            "initial-validation",
            "resource-allocation",
            "timing-analysis",
            "memory-constraints",
        ]
        self.rules = {
            "resource-allocation": [
                self.validate_adc_availability,
                self.pack_channels_to_adcs,
                self.compute_adc_sampling_rate,
                self.compute_cpu_budget,
                self.emit_schedulability,
            ]
        }

    def analyze(self, ir: DAQConfigIR) -> DAQConfigIR:
        for phase in self.phases:
            if phase in self.rules:
                for rule_func in self.rules[phase]:
                    try:
                        # Rules now return a list of Diagnostics or modify ir.semantic_errors directly
                        diagnostics = rule_func(ir)
                        if diagnostics:
                            ir.semantic_errors.extend(diagnostics)
                    except Exception as e:
                        ir.semantic_errors.append(
                            Diagnostic(
                                severity="ERROR",
                                message=f"Unhandled exception in phase {phase}, rule {rule_func.__name__}: {e}",
                                rule_id=rule_func.__name__,
                                suggestion="Check rule implementation for bugs."
                            )
                        )
        return ir

    # --- Resource Allocation Rules ---
    def validate_adc_availability(self, ir: DAQConfigIR) -> List[Diagnostic]:
        diagnostics = []
        total_adc_capacity = sum(res.capacity for res in ir.hardware_resources if res.resource_type == "ADC")
        
        if not ir.channels:
            return diagnostics # No channels requested, no ADC capacity needed

        if len(ir.channels) > total_adc_capacity:
            diagnostics.append(
                Diagnostic(
                    severity="ERROR",
                    message=f"Not enough ADC capacity. Requested {len(ir.channels)} channels, but only {total_adc_capacity} available.",
                    rule_id="validate_adc_availability",
                    suggestion="Reduce the number of requested channels or add more ADC hardware resources."
                )
            )
        return diagnostics

    def pack_channels_to_adcs(self, ir: DAQConfigIR) -> List[Diagnostic]:
        diagnostics = []
        available_adcs = [res for res in ir.hardware_resources if res.resource_type == "ADC"]
        
        if not available_adcs and ir.channels: # If channels are requested but no ADCs are defined
            diagnostics.append(
                Diagnostic(
                    severity="ERROR",
                    message="Channels requested but no ADC hardware resources defined.",
                    rule_id="pack_channels_to_adcs",
                    suggestion="Define ADC hardware resources in the IR."
                )
            )
            return diagnostics

        channel_index = 0
        ir.resource_assignments.clear() # Clear previous assignments if any
        for adc in available_adcs:
            for i in range(adc.capacity):
                if channel_index < len(ir.channels):
                    channel = ir.channels[channel_index]
                    assignment = ResourceAssignment(channel_id=channel, resource_name=adc.name, resource_index=i)
                    ir.resource_assignments.append(assignment)
                    channel_index += 1
                else:
                    break  # All channels assigned
            if channel_index >= len(ir.channels):
                break  # All channels assigned
        
        if channel_index < len(ir.channels): # Should not happen if validate_adc_availability passed
            diagnostics.append(
                Diagnostic(
                    severity="ERROR",
                    message=f"Failed to assign all channels. {len(ir.channels) - channel_index} channels unassigned.",
                    rule_id="pack_channels_to_adcs",
                    suggestion="This indicates an internal logic error or a previous validation failure."
                )
            )
        return diagnostics

    def compute_adc_sampling_rate(self, ir: DAQConfigIR) -> List[Diagnostic]:
        diagnostics = []
        available_adcs = [res for res in ir.hardware_resources if res.resource_type == "ADC"]
        
        # Collect unique ADCs that have channels assigned to them
        used_adc_names = set(assignment.resource_name for assignment in ir.resource_assignments)
        num_adcs_used = len(used_adc_names)

        if num_adcs_used == 0:
            if ir.channels: # If channels are requested but no ADCs were assigned
                diagnostics.append(
                    Diagnostic(
                        severity="WARNING",
                        message="Channels requested but no ADCs were assigned. Cannot compute ADC sampling rates.",
                        rule_id="compute_adc_sampling_rate",
                        suggestion="Ensure ADC hardware resources are defined and channels are packed correctly."
                    )
                )
            return diagnostics

        # Distribute the sampling rate evenly across used ADCs
        # This assumes all used ADCs contribute equally to the overall sample rate
        base_sampling_rate_per_adc = ir.sample_rate / num_adcs_used

        for adc in available_adcs:
            if adc.name in used_adc_names:
                channels_on_adc = [assignment for assignment in ir.resource_assignments if assignment.resource_name == adc.name]
                num_channels_on_adc = len(channels_on_adc)
                
                if num_channels_on_adc > 0:
                    # Effective sampling rate per physical channel on this ADC, considering multiplexing
                    effective_sampling_rate = base_sampling_rate_per_adc / num_channels_on_adc
                    adc.properties["effective_sampling_rate"] = effective_sampling_rate
                    # print(f"ADC {adc.name} effective sampling rate: {effective_sampling_rate:.2f} Hz ({num_channels_on_adc} channels)")
                else:
                    diagnostics.append(
                        Diagnostic(
                            severity="INFO",
                            message=f"ADC {adc.name} is defined but has no channels assigned to it.",
                            rule_id="compute_adc_sampling_rate"
                        )
                    )
        return diagnostics

    def compute_cpu_budget(self, ir: DAQConfigIR) -> List[Diagnostic]:
        diagnostics = []
        CPU_TIME_PER_CHANNEL_MS = 0.1  # milliseconds per channel per sample
        CPU_OVERHEAD_MS = 0.5          # fixed overhead per task

        total_cpu_time_ms = (len(ir.channels) * CPU_TIME_PER_CHANNEL_MS) + CPU_OVERHEAD_MS
        sample_period_ms = 1000 / ir.sample_rate
        cpu_utilization_percent = (total_cpu_time_ms / sample_period_ms) * 100

        ir.target_config["daq_task_cpu_time_ms"] = total_cpu_time_ms
        ir.target_config["daq_task_cpu_utilization_percent"] = cpu_utilization_percent

        if cpu_utilization_percent > 80: 
            diagnostics.append(
                Diagnostic(
                    severity="WARNING",
                    message=f"High CPU utilization ({cpu_utilization_percent:.2f}%) for DAQ task.",
                    rule_id="compute_cpu_budget",
                    suggestion="Consider reducing sample rate or number of channels."
                )
            )
        return diagnostics

    def emit_schedulability(self, ir: DAQConfigIR) -> List[Diagnostic]:
        diagnostics = []
        if "daq_task_cpu_utilization_percent" in ir.target_config:
            cpu_utilization = ir.target_config["daq_task_cpu_utilization_percent"]
            if cpu_utilization > 100:
                diagnostics.append(
                    Diagnostic(
                        severity="ERROR",
                        message=f"DAQ task is unschedulable (CPU utilization: {cpu_utilization:.2f}%).",
                        rule_id="emit_schedulability",
                        suggestion="Reduce sample rate, number of channels, or optimize task execution time."
                    )
                )
            elif cpu_utilization > 90:
                diagnostics.append(
                    Diagnostic(
                        severity="WARNING",
                        message=f"DAQ task has very high CPU utilization ({cpu_utilization:.2f}%).",
                        rule_id="emit_schedulability",
                        suggestion="Risk of missed deadlines. Consider reducing sample rate or channels."
                    )
                )
        return diagnostics

# Example usage (for testing purposes)
if __name__ == "__main__":
    # Create a dummy IR instance
    ir_instance = DAQConfigIR(
        sample_rate=1000,
        channels=[0, 1, 2, 3, 4, 5],
        output_file="test.csv",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4),
            HardwareResource(name="ADC2", resource_type="ADC", capacity=2)
        ]
    )

    analyzer = SemanticAnalyzer()
    analyzed_ir = analyzer.analyze(ir_instance)

    if analyzed_ir.semantic_errors:
        print("Semantic Analysis Errors:")
        for diag in analyzed_ir.semantic_errors:
            print(f"- [{diag.severity}] {diag.rule_id}: {diag.message} (Suggestion: {diag.suggestion})")
    else:
        print("Semantic Analysis Completed Successfully.")
        print(f"Resource Assignments: {analyzed_ir.resource_assignments}")
        for adc in ir_instance.hardware_resources:
            if "effective_sampling_rate" in adc.properties:
                print(f"ADC {adc.name} effective sampling rate: {adc.properties['effective_sampling_rate']:.2f} Hz")
        if "daq_task_cpu_utilization_percent" in ir_instance.target_config:
            print(f"DAQ Task CPU Utilization: {ir_instance.target_config['daq_task_cpu_utilization_percent']:.2f}%")


