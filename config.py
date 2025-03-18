import os

# --- General Configuration ---
LANGUAGE = 1  # 1 = English
IMBUS_TYPE = 8  # IM8 Bus type
SLOT_NUMBERS = [1,]  # Define which slots are used

# --- Probe Slot Configuration ---
# Dictionary where key = slot number, value = measurement type
PROBES = {
    1: "length",  # Alongside
    2: "diameter",  # Example: Slot 2 measures diameter
    3: "diameter",  # Example: Slot 2 measures diameter
    4: "diameter",  # Example: Slot 2 measures diameter
    5: "diameter",  # Example: Slot 2 measures diameter
    6: "diameter",  # Example: Slot 2 measures diameter
    7: "niU",  # Not in Use
    8: "niU",  # Not in Use
}

# --- Path Configuration ---
CODE_PATH = os.path.dirname(os.path.abspath(__file__))  # Path of the scripts
DLL_PATH = r"C:\IBR_DDK\DLL\x64"  # Path where `ibr_ddk.dll` is stored

# --- Define Measurement Campaign Folder ---
MEASUREMENT_CAMPAIGN_PATH = os.path.join(CODE_PATH, "Measurements", "Test")  # Change this for new campaigns
os.makedirs(MEASUREMENT_CAMPAIGN_PATH, exist_ok=True)  # Ensure campaign folder exists

# --- Setup File Location in Campaign Folder ---
SETUP_FILE_PATH = os.path.join(MEASUREMENT_CAMPAIGN_PATH, "My_setup.ddk")
