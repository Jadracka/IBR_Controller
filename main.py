from ibr_ddk import get_dll, get_setup_file

# Retrieve DLL and Setup File
ibr_ddk = get_dll()
SETUP_FILE = get_setup_file()

# --- Configuration Constants ---
LANGUAGE_ENGLISH = 1
TEST_DEVICE = 1
TEST_CHANNEL = 1

# --- Create Setup File ---
setup_result = ibr_ddk.Device_Setup(LANGUAGE_ENGLISH, SETUP_FILE, None, b"")

if setup_result == 0:
    print("Setup file created successfully.")
else:
    print(f"Setup file creation failed with error code: {setup_result}")

# --- Initialize Device ---
init_result = ibr_ddk.Device_InitEx(LANGUAGE_ENGLISH, SETUP_FILE, None, None, None)

if init_result == 0:
    print("Device initialized successfully.")
else:
    print(f"Device initialization failed with error code: {init_result}")

# --- Cleanup ---
ibr_ddk.Device_DeInit()
print("Device deinitialized.")