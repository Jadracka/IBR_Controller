import sys
from time import sleep
from ibrdll import IbrDll


if __name__ == "__main__":

    DLL_FILE = r"C:\IBR_DDK\DLL\x64\ibr_ddk.dll"
    SETUP_FILE = 'C:\IMB_Test\IMB_Test.ddk'
    
    module_number = 1
    gauge_number = 1
    
    ibr = IbrDll(DLL_FILE)
    
    # Gerät initialisieren
    status = ibr.init_device(SETUP_FILE)
    if status != 0:
        print(f"Device_Init Fehler, Rückgabewert: {status}")
        sys.exit(1)
    
    # Geräteversion abrufen
    major, minor = ibr.get_version()
    print(f"IBR DDK Version: {major}.{minor}")
    
    # 20 Werte vom Gerät abrufen, ~1 Sekunde Abstand
    for i in range(20):
        status, value = ibr.get_value(module_number, gauge_number)
        if status != 0:
            print(f"Device_Value Fehler, Rückgabewert: {status}")
        else:
            print("Messwert {:02d}: {:7.4f}".format(i, value))
        sleep(1)
    
    # Gerät deinitialisieren
    status = ibr.deinit_device()
