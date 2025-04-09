import sys
import time
from ibrdll import IbrDll
#import notify
import csv
import os

#CONFIGURATION DON'T TOUCH
DLL_FILE = r"C:\IBR_DDK\DLL\x64\ibr_ddk.dll"
SETUP_FILE = r"C:\IMB_Test\IMB_Test.ddk"

# USER SETTINGS
FREQUENCY_HZ = 1                 # Measurements per second
DURATION_HOURS = 3               # Total duration in hours, can be also None for infinite
MEASUREMENT_INTERVAL = 1 / FREQUENCY_HZ
TOTAL_SECONDS = DURATION_HOURS * 3600

os.makedirs("Measurements", exist_ok=True)
CSV_FILENAME = os.path.join(
    "Measurements", f"measurement_{time.strftime('%Y%m%d_%H%M%S')}.csv")

MESSTASTER_ADDRESSE = [1, 2]#, 3, 4, 5, 6, 7, 8]
MODULE_NUMMER = 1
MESSTASTER_BESCHREIBUNG = {
    1: "Z direction 1",
    2: "Z direction 2",
    3: "Z direction 3",
    4: "X direction 1",
    5: "X direction 2",
    6: "Y direction",
}
#MESSTASTER_BESCHREIBUNG.get(7, "Unknown probe")

ibr = IbrDll(DLL_FILE)

#FUNCTION DEFINITIONS
def value_reading(module_number, gauge_number):
    """
    Liest den Wert des Messgeräts aus.
    
    :param module_number: Modulnummer
    :param gauge_number: Messgerät Nummer
    :return: Status und Wert des Messgeräts
    """
    status, value = ibr.get_value(module_number, gauge_number)
    if status != 0:
        MeasurementError = f"Gauge #{gauge_number}: {status}"
        if status == 136:
            #notify.me(f"Gauge #{gauge_number} out of range")
            print(f"Gauge #{gauge_number} ({MESSTASTER_BESCHREIBUNG.get(gauge_number, 'Unknown')}) out of range")
        else:
            print(f"Error {status} on {gauge_number} ({MESSTASTER_BESCHREIBUNG.get(gauge_number, 'Unknown')})")
            #notify.me(MeasurementError)
        return None
    else:
        return value



if __name__ == "__main__":

    header = ["Time"] + [MESSTASTER_BESCHREIBUNG.get(addr, f"Gauge {addr}: {MESSTASTER_BESCHREIBUNG.get(addr)}") for addr in MESSTASTER_ADDRESSE]
    
    #Gerät initialisieren
    status = ibr.init_device(SETUP_FILE)
    if status != 0:
        print(f"Device_Init Fehler, Rückgabewert: {status}")
        sys.exit(1)
    else:
        print(f"Starting measurement for {DURATION_HOURS} hour(s) at {FREQUENCY_HZ} Hz")

    start_time = time.time()
    end_time = None if DURATION_HOURS is None else start_time + (DURATION_HOURS * 3600)

    try:
        with open(CSV_FILENAME, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)

            while end_time is None or time.time() < end_time:
                now = time.strftime('%Y-%m-%d %H:%M:%S')
                row = [now]

                for addr in MESSTASTER_ADDRESSE:
                    value = value_reading(MODULE_NUMMER, addr)
                    if value is not None:
                        row.append(f"{value:.4f}")
                    else:
                        row.append("error")

                writer.writerow(row)
                print(" | ".join(row))
                time.sleep(MEASUREMENT_INTERVAL)

    except KeyboardInterrupt:
        print("\n❗ Measurement cancelled by user.")
        #notify.me("❌ Measurement manually cancelled.")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        #notify.me(f"❌ Measurement crashed! {e}")

    finally:
        status = ibr.deinit_device()
        if status != 0:
            print(f"Device_Deinit Fehler, Rückgabewert: {status}")
        else:
            print("🔌 Device deinitialized.")

        #notify.me("Measurement finished.")
        print(f"📁 CSV saved to: {CSV_FILENAME}")
        

        # Gerät deinitialisieren
        status = ibr.deinit_device()