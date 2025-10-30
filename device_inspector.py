
# This flag will be used by the GUI to check if NI-DAQmx is available.
NIDAQMX_AVAILABLE = False

try:
    import nidaqmx
    from nidaqmx.system import System
    NIDAQMX_AVAILABLE = True
except (ImportError, nidaqmx.errors.DaqError):
    # This will catch errors if nidaqmx is not installed OR if the driver is not found.
    pass

import serial.tools.list_ports

# --- NI-DAQmx Functions ---

def get_nidaqmx_devices():
    """Returns a list of NI DAQ device names connected to the system."""
    if not NIDAQMX_AVAILABLE:
        return []
    try:
        # Using a timeout to prevent long waits if the driver is in a bad state.
        system = System.local()
        return system.devices.device_names
    except nidaqmx.errors.DaqError:
        return []

def get_ai_physical_channels(device_name):
    """Returns a list of physical analog input channels for a given NI-DAQmx device."""
    if not NIDAQMX_AVAILABLE: return []
    try:
        device = System.local().devices[device_name]
        return device.ai_physical_chans.channel_names
    except (nidaqmx.errors.DaqError, KeyError):
        return []

def get_max_ai_sample_rate(device_name):
    """Returns the maximum single-channel analog input sample rate for an NI-DAQmx device."""
    if not NIDAQMX_AVAILABLE: return 0.0
    try:
        device = System.local().devices[device_name]
        return device.ai_max_single_chan_rate
    except (nidaqmx.errors.DaqError, KeyError):
        return 0.0

# --- Serial Port Functions ---

def get_serial_ports():
    """Returns a list of available serial COM ports."""
    try:
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except Exception:
        return []
