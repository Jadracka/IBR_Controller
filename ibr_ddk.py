import os
import ctypes
import config as cg  # Import config settings

# --- Define DLL Location ---
SETUP_FILE = cg.SETUP_FILE_PATH.encode()  # Convert string path to bytes

try:
    os.add_dll_directory(cg.DLL_PATH)  # Ensure Python searches in the DLL folder
    ibr_ddk = ctypes.windll.LoadLibrary(os.path.join(cg.DLL_PATH, "ibr_ddk.dll"))
except OSError as e:
    print(f"Error: Could not load ibr_ddk.dll from {cg.DLL_PATH}. Details: {e}")
    exit(1)

# --- Define Function Prototypes ---
ibr_ddk.Device_SetInt.argtypes = [ctypes.c_short, ctypes.c_short]
ibr_ddk.Device_SetInt.restype = ctypes.c_short

# Expose DLL and Setup File for Use in Other Scripts
def get_dll():
    return ibr_ddk

def get_setup_file():
    return SETUP_FILE