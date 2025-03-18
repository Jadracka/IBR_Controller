import os
import ctypes
import csv
import time
from ibr_ddk import get_dll, get_setup_file
import config as cg  # Import config settings

# Retrieve DLL and Setup File
ibr_ddk = get_dll()
SETUP_FILE = get_setup_file()

print(f"Using setup file: {SETUP_FILE.decode()}")
print(f"Measurement campaign path: {cg.MEASUREMENT_CAMPAIGN_PATH}")

# Ensure the campaign folder exists
if not os.path.exists(cg.MEASUREMENT_CAMPAIGN_PATH):
    os.makedirs(cg.MEASUREMENT_CAMPAIGN_PATH, exist_ok=True)
    print(f"📁 Created missing measurement campaign folder: {cg.MEASUREMENT_CAMPAIGN_PATH}")

# Manually create an empty setup file before calling Device_Setup
if not os.path.exists(SETUP_FILE.decode()):
    print(f"📄 Manually creating empty setup file: {SETUP_FILE.decode()}")
    with open(SETUP_FILE.decode(), "w") as f:
        f.write("")  # Create an empty file
    print(f"✅ Setup file manually created.")

# Explicitly close the setup file before calling Device_Setup
try:
    with open(SETUP_FILE.decode(), "r") as f:
        pass  # Open and close the file to ensure it's not locked
    print(f"✅ Setup file closed properly before Device_Setup().")
except Exception as e:
    print(f"❌ Failed to close setup file: {e}")

time.sleep(1)  # Small delay to prevent race conditions

# --- Step 1: Try Opening the Setup File First ---
open_result = ibr_ddk.Device_OpenSetup(SETUP_FILE)

if open_result == 0:
    print("✅ Setup file opened successfully.")
else:
    print(f"❌ Failed to open setup file. Error code: {open_result}")
    exit(1)

# --- Step 2: Configure IMBus Type, USB Address, and Instrument Type ---
ibr_ddk.Device_SetInt(ctypes.c_short(0), ctypes.c_short(2))  # ✅ Corrected
ibr_ddk.Device_SetInt(ctypes.c_short(2), ctypes.c_short(0))  # ✅ USB Address (No selection)
ibr_ddk.Device_SetInt(ctypes.c_short(4), ctypes.c_short(301))  # ✅ IMBus Instrument type
ibr_ddk.Device_SetInt(ctypes.c_short(17), ctypes.c_short(0))  # ✅ IMB-usb connection type


print("✅ IMBus type and address set successfully.")

# --- Step 3: Verify Setup File Values ---
addresses = [0, 2, 4, 17]  # Key addresses for IMBus setup
for addr in addresses:
    value = ctypes.c_short()
    ret = ibr_ddk.Device_GetInt(addr, ctypes.byref(value))
    if ret == 0:
        print(f"✅ Address {addr}: {value.value}")
    else:
        print(f"❌ Failed to read Address {addr}, Error Code: {ret}")

# --- Step 4: Initialize Probes for Defined Slots ---
for slot in cg.SLOT_NUMBERS:
    measurement_type = cg.PROBES.get(slot, "unknown")  # Get measurement type
    ibr_ddk.Device_SetInt(slot, ctypes.c_short(30))  # Measuring input exists with connected gauge
    ibr_ddk.Device_SetInt(slot, ctypes.c_short(32))  # IMBus module type (adjust based on module)

    print(f"✅ Slot {slot} initialized for {measurement_type}.")

# --- Step 5: Close the Setup File ---
ibr_ddk.Device_CloseSetup()
print("✅ Setup file configuration completed.")

# --- Step 6: Prepare Device for Measurements ---
ibr_ddk.Device_PreInit(0, 0, 0, 0, 0, 0, 0)  # Ensure correct pre-initialization
ibr_ddk.Device_AdressOnOff(1, 0, 1)  # Enable all measurement channels

probe_info = ctypes.create_string_buffer(200)  # Buffer for probe name
probe_check = ibr_ddk.Device_GetName(1, SETUP_FILE, 1, 2, 1, probe_info)  # Check Addr1.1

if probe_check == 0:
    print(f"✅ Probe assigned at Addr1.1: {probe_info.value.decode()}")
else:
    print(f"❌ Probe setup might be incorrect at Addr1.1, Error Code: {probe_check}")

# --- Step 7: Initialize the Device ---
init_result = ibr_ddk.Device_InitEx(cg.LANGUAGE, SETUP_FILE, None, None, None)

if init_result == 0:
    print("✅ Device initialized successfully.")
else:
    print(f"❌ Device initialization failed with error code: {init_result}")
    exit(1)

# --- Step 8: Start Taking Measurements ---
print("📏 Starting measurements...")

# Prepare CSV file to store measurements
csv_file = os.path.join(cg.MEASUREMENT_CAMPAIGN_PATH, "measurements.csv")
with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp"] + [f"Slot {slot} ({measurement})" for slot, measurement in cg.PROBES.items()])

    # Collect 10 measurements (adjust as needed)
    for i in range(10):
        row = [time.strftime("%Y-%m-%d %H:%M:%S")]
        for slot in cg.SLOT_NUMBERS:
            measurement = ctypes.c_double(0.0)
            ret = ibr_ddk.Device_Value(slot, 1, ctypes.byref(measurement))  # Read from channel 1

            if ret == 0:
                row.append(measurement.value)
                print(f"📊 Slot {slot} ({cg.PROBES.get(slot, 'unknown')}): {measurement.value}")
            else:
                row.append("Error")
                print(f"❌ Failed to read from Slot {slot}, Error Code: {ret}")

        writer.writerow(row)
        time.sleep(1)  # Wait 1 second between measurements

print(f"✅ Measurements saved to {csv_file}")

# --- Step 9: Cleanup ---
ibr_ddk.Device_DeInit()
print("✅ Device deinitialized.")
