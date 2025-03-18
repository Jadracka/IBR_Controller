import os
from ibr_ddk import get_dll, get_setup_file
import config as cg  # Import config settings

# Retrieve DLL and Setup File
ibr_ddk = get_dll()
SETUP_FILE = get_setup_file()

print(f"Using setup file: {SETUP_FILE.decode()}")
print(f"Measurement campaign path: {cg.MEASUREMENT_CAMPAIGN_PATH}")

# --- Step 1: Open the Setup File ---
open_result = ibr_ddk.Device_OpenSetup(SETUP_FILE)

if open_result == 0:
    print("Setup file opened successfully.")
else:
    print(f"Failed to open setup file. Error code: {open_result}")
    exit(1)

# --- Step 2: Configure the IMBus Type ---
write_result = ibr_ddk.Device_SetInt(1, cg.IMBUS_TYPE)  # Set IMBus type

if write_result == 0:
    print(f"IMBus type set to {cg.IMBUS_TYPE} successfully.")
else:
    print(f"Failed to set IMBus type. Error code: {write_result}")
    exit(1)

# --- Step 3: Initialize Probes for Defined Slots ---
for slot in cg.SLOT_NUMBERS:
    measurement_type = cg.PROBES.get(slot, "unknown")  # Get measurement type
    slot_assign_result = ibr_ddk.Device_SetInt(slot, 2)  # Assign Slot for measurement

    if slot_assign_result == 0:
        print(f"Slot {slot} initialized successfully for {measurement_type}.")
    else:
        print(f"Failed to initialize Slot {slot}. Error code: {slot_assign_result}")
        exit(1)

# --- Step 4: Close the Setup File ---
ibr_ddk.Device_CloseSetup()
print("Setup file configuration completed.")
