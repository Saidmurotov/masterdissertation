from daq_config import DAQConfig
from code_generator import generate_code
from device_inspector import (
    get_connected_devices,
    get_ai_physical_channels,
    get_max_ai_sample_rate,
)

def select_device(devices):
    """Asks the user to select a device from a list."""
    if not devices:
        return None
    print("\nAvailable DAQ devices:")
    for i, device in enumerate(devices):
        print(f"  {i + 1}: {device}")
    
    while True:
        try:
            choice = int(input("Select a device (number): "))
            if 1 <= choice <= len(devices):
                return devices[choice - 1]
            else:
                print("Invalid number. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    """Main function to run the intelligent DAQ code generator."""
    print("--- Intelligent DAQ Code Generator ---")

    # 1. Find and select a device
    connected_devices = get_connected_devices()
    if not connected_devices:
        print("\nError: No NI-DAQmx devices found.")
        print("Please ensure a device is connected and NI-DAQmx drivers are installed.")
        return

    device_name = select_device(connected_devices)
    if not device_name:
        # This case might happen if user input is invalid in select_device, though it's handled.
        return

    print(f"\nSelected device: {device_name}")

    # 2. Inspect device capabilities
    available_channels = get_ai_physical_channels(device_name)
    max_rate = get_max_ai_sample_rate(device_name)

    if not available_channels:
        print(f"Error: Could not find any analog input channels on {device_name}.")
        return

    print(f"Max Sample Rate: {max_rate:.0f} Hz")
    print(f"Available Channels: {[ch.split('/')[-1] for ch in available_channels]}")

    try:
        # 3. Get validated configuration from user
        sample_rate = int(input(f"Enter Sample Rate (Hz, max {max_rate:.0f}): "))
        if sample_rate > max_rate:
            print(f"Warning: Sample rate exceeds the device's maximum. Clamping to {max_rate:.0f} Hz.")
            sample_rate = max_rate

        channels_str = input("Enter channel numbers to use (e.g., 0,1,3): ")
        output_file = input("Enter the output file name (e.g., data.csv): ")

        # Validate and parse channels
        chosen_channels = []
        available_channel_nums = [int(ch.split('ai')[-1]) for ch in available_channels]
        for c_str in channels_str.split(','):
            c = int(c_str.strip())
            if c in available_channel_nums:
                chosen_channels.append(c)
            else:
                raise ValueError(f"Channel 'ai{c}' is not available on {device_name}.")

        # 4. Create config and generate code
        config = DAQConfig(
            sample_rate=sample_rate, 
            channels=chosen_channels, 
            output_file=output_file
        )

        print("\nGenerating code...")
        generated_script = generate_code(config, device_name)

        print("Code generated successfully!")
        print("--------------------------------------------------")
        print(generated_script)
        print("--------------------------------------------------")

        save_choice = input("\nSave this script to a file? (y/n): ").lower()
        if save_choice == 'y':
            file_name = input("Enter file name (e.g., my_daq_script.py): ")
            if not file_name.endswith(".py"): file_name += ".py"
            with open(file_name, "w") as f:
                f.write(generated_script)
            print(f"Script saved as '{file_name}'")

    except ValueError as e:
        print(f"\nInput Error: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
