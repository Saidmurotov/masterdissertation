class DAQConfig:
    def __init__(self, sample_rate, channels, output_file):
        self.sample_rate = sample_rate
        self.channels = channels
        self.output_file = output_file

    def display_config(self):
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"Channels: {self.channels}")
        print(f"Output File: {self.output_file}")

    def validate_config(self):
        if self.sample_rate <= 0:
            raise ValueError("Sample rate must be positive.")
        if not self.channels:
            raise ValueError("Channels list cannot be empty.")
        if not self.output_file:
            raise ValueError("Output file name cannot be empty.")
        print("Configuration is valid.")

# Example usage:
# try:
#     config = DAQConfig(sample_rate=1000, channels=[1, 2, 5], output_file="data.csv")
#     config.validate_config()
#     config.display_config()
# except ValueError as e:
#     print(f"Error: {e}")
