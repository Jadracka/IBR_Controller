import os
import ctypes

# --- Define DLL Location ---
DLL_FOLDER = r"C:\IBR_DDK\DLL\x64"  # Make sure this is correct!
SCRIPT_FOLDER = os.path.dirname(os.path.abspath(__file__))  # Get script's directory
SETUP_FILE = os.path.join(SCRIPT_FOLDER, "My_setup.DDK").encode()  # Store setup file in script folder


try:
    os.add_dll_directory(DLL_FOLDER)  # Ensure Python searches in the right place
    ibr_ddk = ctypes.windll.LoadLibrary(os.path.join(DLL_FOLDER, "ibr_ddk.dll"))
except OSError as e:
    print(f"Error: Could not load ibr_ddk.dll. Details: {e}")
    exit(1)

# --- Define Function Prototypes ---
ibr_ddk.Device_InitEx.argtypes = [ctypes.c_short, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
ibr_ddk.Device_InitEx.restype = ctypes.c_short

ibr_ddk.Device_Value.argtypes = [ctypes.c_short, ctypes.c_short, ctypes.POINTER(ctypes.c_double)]
ibr_ddk.Device_Value.restype = ctypes.c_short

ibr_ddk.Device_DeInit.argtypes = []
ibr_ddk.Device_DeInit.restype = ctypes.c_short

ibr_ddk.Device_Setup.argtypes = [ctypes.c_short, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char_p]
ibr_ddk.Device_Setup.restype = ctypes.c_short

# Expose DLL and Setup File for Use in Other Scripts
def get_dll():
    return ibr_ddk

def get_setup_file():
    return SETUP_FILE
