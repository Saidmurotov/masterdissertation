
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import json
from collections import deque
import numpy as np
from numpy.fft import fft, fftfreq

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import all necessary functions from our other modules
from device_inspector import (
    NIDAQMX_AVAILABLE,
    get_nidaqmx_devices,
    get_ai_physical_channels,
    get_max_ai_sample_rate,
    get_serial_ports
)
from daq_config import DAQConfig
from code_generator import generate_code

class DaqApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Universal DAQ Code Generator & Simulator")
        self.geometry("1100x750")
        self.minsize(800, 600)

        self.device_info = {}
        self.simulation_running = False
        self.sim_after_id = None
        self.sim_data = {}
        self.sim_time = deque(maxlen=200)

        self.main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)

        self.controls_frame = ttk.Frame(self.main_pane, padding="10")
        self.main_pane.add(self.controls_frame, weight=2)

        self.sim_frame = ttk.LabelFrame(self.main_pane, text="Live Simulation & Analysis", padding="10")
        self.main_pane.add(self.sim_frame, weight=3)

        self.create_control_widgets(self.controls_frame)
        self.create_simulation_widgets(self.sim_frame)
        
        # Set initial device type and trigger scan
        if NIDAQMX_AVAILABLE:
            self.device_type_combo.current(0)
        else:
            # Find the index of "Simulation Only" and set it as default
            try:
                sim_only_index = self.device_type_combocget('values').index("Simulation Only")
                self.device_type_combo.current(sim_only_index)
            except ValueError:
                self.device_type_combo.current(0) # Fallback

        self.on_device_type_select(None)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_control_widgets(self, parent):
        parent.rowconfigure(2, weight=1)
        parent.columnconfigure(0, weight=1)

        device_frame = ttk.LabelFrame(parent, text="1. Device Configuration", padding="10")
        device_frame.grid(row=0, column=0, sticky="ew", pady=5)
        device_frame.columnconfigure(1, weight=1)

        device_types = ["Serial", "Simulation Only", "LabJack (soon)"]
        if NIDAQMX_AVAILABLE:
            device_types.insert(0, "NI-DAQmx")

        ttk.Label(device_frame, text="Device Type:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.device_type_combo = ttk.Combobox(device_frame, state="readonly", values=device_types)
        self.device_type_combo.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.device_type_combo.bind("<<ComboboxSelected>>", self.on_device_type_select)

        ttk.Label(device_frame, text="Device:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.device_combobox = ttk.Combobox(device_frame, state="readonly")
        self.device_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.device_combobox.bind("<<ComboboxSelected>>", self.on_device_select)
        self.scan_button = ttk.Button(device_frame, text="Rescan", command=self.scan_for_devices)
        self.scan_button.grid(row=1, column=2, padx=5, pady=5)
        self.device_info_label = ttk.Label(device_frame, text="Select a device...", foreground="blue")
        self.device_info_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        self.params_frame = ttk.LabelFrame(parent, text="2. DAQ Parameters", padding="10")
        self.params_frame.grid(row=1, column=0, sticky="ew", pady=5)
        self.params_frame.columnconfigure(1, weight=1)

        ttk.Label(self.params_frame, text="Sample Rate (Hz):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sample_rate_entry = ttk.Entry(self.params_frame)
        self.sample_rate_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.params_frame, text="Channels/Values:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.channels_entry = ttk.Entry(self.params_frame)
        self.channels_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.params_frame, text="Output File:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.output_file_entry = ttk.Entry(self.params_frame)
        self.output_file_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.output_file_entry.insert(0, "daq_data.csv")

        self.baud_rate_label = ttk.Label(self.params_frame, text="Baud Rate:")
        self.baud_rate_combo = ttk.Combobox(self.params_frame, values=["9600", "19200", "38400", "57600", "115200"], state="readonly")
        self.baud_rate_combo.set("9600")

        config_button_frame = ttk.Frame(self.params_frame)
        config_button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        self.save_config_button = ttk.Button(config_button_frame, text="Save Config...", command=self.save_configuration)
        self.save_config_button.pack(side=tk.LEFT, padx=5)
        self.load_config_button = ttk.Button(config_button_frame, text="Load Config...", command=self.load_configuration)
        self.load_config_button.pack(side=tk.LEFT, padx=5)

        codegen_frame = ttk.LabelFrame(parent, text="3. Generated Code", padding="10")
        codegen_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        codegen_frame.rowconfigure(1, weight=1)
        codegen_frame.columnconfigure(0, weight=1)

        self.generate_button = ttk.Button(codegen_frame, text="Generate Code", command=self.generate_daq_code)
        self.generate_button.grid(row=0, column=0, pady=5, sticky="ew")
        self.code_text = tk.Text(codegen_frame, wrap="word", height=10, font=("Courier New", 9))
        self.code_text.grid(row=1, column=0, sticky="nsew")
        self.save_button = ttk.Button(codegen_frame, text="Save Code...", command=self.save_code_to_file, state="disabled")
        self.save_button.grid(row=2, column=0, pady=5, sticky="ew")
        
        self.set_widget_states("disabled")

    def create_simulation_widgets(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        sim_controls_frame = ttk.Frame(parent)
        sim_controls_frame.grid(row=0, column=0, sticky="ew", pady=5)
        self.start_sim_button = ttk.Button(sim_controls_frame, text="Start Simulation", command=self.start_simulation, state="disabled")
        self.start_sim_button.pack(side=tk.LEFT, padx=5)
        self.stop_sim_button = ttk.Button(sim_controls_frame, text="Stop Simulation", command=self.stop_simulation, state="disabled")
        self.stop_sim_button.pack(side=tk.LEFT, padx=5)

        self.fig = Figure(figsize=(5, 6), dpi=100)
        self.ax_time = self.fig.add_subplot(2, 1, 1)
        self.ax_fft = self.fig.add_subplot(2, 1, 2)
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew")

    def set_widget_states(self, state):
        for child in self.params_frame.winfo_children():
            if isinstance(child, (ttk.Entry, ttk.Combobox, ttk.Button)):
                child.configure(state=state)
        self.generate_button.configure(state=state)
        if hasattr(self, 'start_sim_button'):
            self.start_sim_button.configure(state=state)
        self.load_config_button.configure(state="normal")

    def on_device_type_select(self, event):
        self.update_parameter_visibility()
        self.scan_for_devices()

    def update_parameter_visibility(self):
        device_type = self.device_type_combo.get()
        if device_type == "Serial":
            self.baud_rate_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
            self.baud_rate_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        else:
            self.baud_rate_label.grid_remove()
            self.baud_rate_combo.grid_remove()

    def scan_for_devices(self):
        device_type = self.device_type_combo.get()
        self.device_combobox.set("")
        self.device_combobox['values'] = []
        self.device_info_label.config(text="")
        self.set_widget_states("disabled")

        try:
            if device_type == "NI-DAQmx":
                devices = get_nidaqmx_devices()
                self.device_combobox['values'] = devices
                if devices:
                    self.device_combobox.current(0)
                    self.on_device_select(None)
                else:
                    self.device_info_label.config(text="No NI-DAQmx devices found. Please install drivers or check connection.", foreground="orange")
            elif device_type == "Serial":
                ports = get_serial_ports()
                self.device_combobox['values'] = ports
                if ports:
                    self.device_combobox.current(0)
                    self.on_device_select(None)
                else:
                    self.device_info_label.config(text="No COM ports found.", foreground="orange")
            elif device_type == "Simulation Only":
                self.device_info_label.config(text="Ready for simulation. No device needed.", foreground="blue")
                self.set_widget_states("normal")
                self.generate_button.config(state="disabled")
            else:
                self.device_info_label.config(text=f"{device_type} support is not yet implemented.", foreground="red")
        except Exception as e:
            messagebox.showerror("Scan Error", f"An error occurred while scanning for devices: {e}")

    def on_device_select(self, event):
        device_type = self.device_type_combo.get()
        device_name = self.device_combobox.get()
        if not device_name: return

        try:
            if device_type == "NI-DAQmx":
                max_rate = get_max_ai_sample_rate(device_name)
                channels = get_ai_physical_channels(device_name)
                channel_nums = sorted([int(ch.split('ai')[-1]) for ch in channels])
                self.device_info = {"max_rate": max_rate, "channels": channel_nums}
                info_text = f"Max Rate: {max_rate:.0f} Hz | Available Channels: {channel_nums}"
                self.device_info_label.config(text=info_text, foreground="blue")
                self.set_widget_states("normal")
            elif device_type == "Serial":
                self.device_info = {}
                self.device_info_label.config(text=f"Selected Port: {device_name}", foreground="blue")
                self.set_widget_states("normal")
        except Exception as e:
            messagebox.showerror("Device Error", f"Could not get info for {device_name}: {e}")

    def _validate_inputs(self):
        device_type = self.device_type_combo.get()
        device_name = self.device_combobox.get()
        
        try:
            sample_rate = int(self.sample_rate_entry.get())
            if sample_rate <= 0: raise ValueError("Sample rate must be positive.")
        except ValueError:
            raise ValueError("Sample rate must be a valid integer.")

        try:
            channels_str = self.channels_entry.get()
            if device_type == "Serial":
                num_values = int(channels_str)
                if num_values <= 0: raise ValueError("Number of values must be positive.")
                chosen_channels = list(range(num_values))
            else:
                chosen_channels = [int(c.strip()) for c in channels_str.split(',') if c.strip()]
                if not chosen_channels: raise ValueError("Channel list cannot be empty.")
        except ValueError:
            raise ValueError("Invalid channel/value format.")
        
        baud_rate = int(self.baud_rate_combo.get()) if device_type == "Serial" else None
        output_file = self.output_file_entry.get()
        if not output_file: raise ValueError("Output file name cannot be empty.")

        if device_type == "NI-DAQmx" and device_name:
            if sample_rate > self.device_info.get("max_rate", float('inf')):
                raise ValueError(f"Sample rate exceeds device maximum.")
            for c in chosen_channels:
                if c not in self.device_info.get("channels", []):
                    raise ValueError(f"Channel 'ai{c}' is not available on {device_name}.")
        
        return sample_rate, chosen_channels, output_file, device_name, device_type, baud_rate

    def generate_daq_code(self):
        try:
            sample_rate, channels, output_file, device_name, device_type, baud_rate = self._validate_inputs()
            
            if device_type == "Simulation Only":
                messagebox.showinfo("Info", "Code generation is not applicable for Simulation Only mode.")
                return
            if not device_name:
                messagebox.showerror("Error", "A specific device must be selected to generate code.")
                return

            config = DAQConfig(sample_rate=sample_rate, channels=channels, output_file=output_file)
            
            generated_script = generate_code(
                device_type=device_type, 
                config=config, 
                device_name=device_name, 
                baud_rate=baud_rate
            )
            
            self.code_text.delete("1.0", tk.END)
            self.code_text.insert("1.0", generated_script)
            self.save_button.config(state="normal")
        except (ValueError, NotImplementedError) as e:
            messagebox.showerror("Input Error", str(e))

    def start_simulation(self):
        try:
            sample_rate, channels, _, _, _, _ = self._validate_inputs()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        self.simulation_running = True
        
        if hasattr(self, 'start_sim_button'):
            self.start_sim_button.config(state="disabled")
        if hasattr(self, 'stop_sim_button'):
            self.stop_sim_button.config(state="normal")

        self.set_widget_states("disabled")

        self.sim_channels = channels
        self.sim_rate = sample_rate
        self.sim_time.clear()
        self.sim_data = {ch: deque(maxlen=200) for ch in self.sim_channels}
        self.plot_lines = {}

        self.ax_time.clear()
        self.ax_fft.clear()
        self.ax_time.set_title("Time Domain Signal")
        self.ax_time.set_ylabel("Voltage (V)")
        self.ax_time.grid(True)
        self.ax_fft.set_title("Frequency Domain (FFT)")
        self.ax_fft.set_xlabel("Frequency (Hz)")
        self.ax_fft.set_ylabel("Amplitude")
        self.ax_fft.grid(True)

        for ch in self.sim_channels:
            self.plot_lines[ch], = self.ax_time.plot([], [], label=f"Channel {ch}")
        self.ax_time.legend()
        self.fft_plot_line, = self.ax_fft.plot([], [], color='orange')
        self.fig.tight_layout(pad=2.0)

        self.sim_start_time = np.datetime64('now')
        self.update_simulation()

    def update_simulation(self):
        if not self.simulation_running: return

        current_time = (np.datetime64('now') - self.sim_start_time) / np.timedelta64(1, 's')
        self.sim_time.append(current_time)

        for ch in self.sim_channels:
            noise = random.uniform(-0.1, 0.1)
            value = 2.5 + (ch+1)*np.sin(2 * np.pi * (ch*2+1) * current_time) + noise
            self.sim_data[ch].append(value)
            self.plot_lines[ch].set_data(self.sim_time, self.sim_data[ch])

        self.ax_time.relim()
        self.ax_time.autoscale_view()

        if len(self.sim_time) > 10:
            if not self.sim_channels:
                return
            first_channel = self.sim_channels[0]
            signal = np.array(self.sim_data[first_channel])
            N = len(signal)
            if N > 1:
                T = 1.0 / self.sim_rate
                yf = fft(signal)
                xf = fftfreq(N, T)[:N//2]
                fft_magnitude = 2.0/N * np.abs(yf[0:N//2])
                self.fft_plot_line.set_data(xf, fft_magnitude)
                self.ax_fft.relim()
                self.ax_fft.autoscale_view()

        self.canvas.draw()
        self.sim_after_id = self.after(int(1000 / self.sim_rate), self.update_simulation)

    def stop_simulation(self):
        if self.sim_after_id: self.after_cancel(self.sim_after_id)
        self.simulation_running = False
        
        if hasattr(self, 'start_sim_button'):
            self.start_sim_button.config(state="normal")
        if hasattr(self, 'stop_sim_button'):
            self.stop_sim_button.config(state="disabled")

        self.set_widget_states("normal")

    def save_code_to_file(self):
        code = self.code_text.get("1.0", tk.END)
        if not code.strip():
            messagebox.showwarning("Warning", "There is no code to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python Files", "*.py")])
        if file_path:
            with open(file_path, "w") as f: f.write(code)
            messagebox.showinfo("Success", f"Code saved to {file_path}")

    def save_configuration(self):
        try:
            config_data = {
                "device_type": self.device_type_combo.get(),
                "device_name": self.device_combobox.get(),
                "sample_rate": self.sample_rate_entry.get(),
                "channels": self.channels_entry.get(),
                "output_file": self.output_file_entry.get(),
                "baud_rate": self.baud_rate_combo.get()
            }
            file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(config_data, f, indent=4)
                messagebox.showinfo("Success", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")

    def load_configuration(self):
        try:
            file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
            if file_path:
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
                
                self.device_type_combo.set(config_data.get("device_type", ""))
                self.update_parameter_visibility()
                self.device_combobox.set(config_data.get("device_name", ""))
                self.sample_rate_entry.delete(0, tk.END)
                self.sample_rate_entry.insert(0, config_data.get("sample_rate", ""))
                self.channels_entry.delete(0, tk.END)
                self.channels_entry.insert(0, config_data.get("channels", ""))
                self.output_file_entry.delete(0, tk.END)
                self.output_file_entry.insert(0, config_data.get("output_file", ""))
                self.baud_rate_combo.set(config_data.get("baud_rate", "9600"))
                
                self.on_device_select(None)
                messagebox.showinfo("Success", "Configuration loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")

    def on_closing(self):
        if self.simulation_running:
            self.stop_simulation()
        self.destroy()

if __name__ == "__main__":
    try:
        app = DaqApp()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Failed to start application: {e}")
