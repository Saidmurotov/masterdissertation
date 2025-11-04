import argparse
from src.ir import DAQConfigIR, HardwareResource
from src.semantic_analyzer import SemanticAnalyzer, Diagnostic
from src.generator import CodeGenerator

def main():
    parser = argparse.ArgumentParser(description="DAQ Code Generator and Semantic Analyzer.")
    parser.add_argument("spec_file", help="Path to the YAML specification file.")
    parser.add_argument("output_dir", help="Path to the output directory for generated code.")
    parser.add_argument("--target", default="tiny-rtos", help="Target platform for code generation (e.g., tiny-rtos).")
    parser.add_argument("--explain", action="store_true", help="Enable explain/tracing mode for semantic analysis.")
    
    args = parser.parse_args()

    # TODO: Load IR from spec_file (YAML parsing)
    # For now, create a dummy IR instance for demonstration
    ir_instance = DAQConfigIR(
        sample_rate=1000,
        channels=[0, 1, 2, 3, 4, 5],
        output_file="generated_daq_code",
        hardware_resources=[
            HardwareResource(name="ADC1", resource_type="ADC", capacity=4),
            HardwareResource(name="ADC2", resource_type="ADC", capacity=2)
        ],
        target_config={
            "rtos_task_priority": 3,
            "rtos_stack_size": 512,
            "rtos_tick_rate": 1000,
            "microcontroller_name": "STM32F4"
        }
    )

    analyzer = SemanticAnalyzer()
    analyzed_ir = analyzer.analyze(ir_instance)

    if args.explain:
        print("--- Semantic Analysis Explanation Mode ---")
        # TODO: Implement detailed tracing/explanation here
        # For now, just print diagnostics

    if analyzed_ir.semantic_errors:
        print("Semantic Analysis Issues Found:")
        for diag in analyzed_ir.semantic_errors:
            print(f"  [{diag.severity}] {diag.rule_id}: {diag.message}")
            if diag.suggestion:
                print(f"    Suggestion: {diag.suggestion}")
            if diag.location:
                print(f"    Location: {diag.location}")
        return # Stop if there are errors

    print("Semantic Analysis Completed Successfully.")

    # Generate code
    generator = CodeGenerator()
    try:
        generated_files = generator.generate(analyzed_ir, args.target)
        for filename, content in generated_files.items():
            with open(f"{args.output_dir}/{filename}", "w") as f:
                f.write(content)
            print(f"Generated {filename} in {args.output_dir}/")
    except NotImplementedError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
