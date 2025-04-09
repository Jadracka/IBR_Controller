# -*- coding: utf-8 -*-
"""
Created on Thu Mar 27 17:00:24 2025

@author: schloe
"""
import ctypes
from ctypes import c_short, c_char_p, c_void_p, c_double, POINTER, byref


class IbrDll:
    def __init__(self, dll_path: str):
        """
        :param dll_path: Pfad zur DLL-Datei
        """
        try:
            # DLL laden
            self.dll = ctypes.CDLL(dll_path)
        except OSError as e:
            raise RuntimeError(f"Fehler beim Laden der DLL: {e}")
        
        # Device_Init definieren
        self.Device_Init = self.dll.Device_Init
        self.Device_Init.restype = c_short  # Rückgabewert
        self.Device_Init.argtypes = [c_short, c_char_p, c_void_p, c_void_p] # Argumente

        # Device_GetVersion definieren
        self.Device_GetVersion = self.dll.Device_GetVersion
        self.Device_GetVersion.restype = None
        self.Device_GetVersion.argtypes = [POINTER(c_short), POINTER(c_short)]

        # Device_Value definieren
        self.Device_Value = self.dll.Device_Value
        self.Device_Value.restype = c_short
        self.Device_Value.argtypes = [c_short, c_short, POINTER(c_double)]
        
        # Device_DeInit definieren
        self.Device_DeInit = self.dll.Device_DeInit
        self.Device_DeInit.restype = c_short
        self.Device_DeInit.argtypes = []

        # Status ob das Gerät initialisiert wurde
        self.initialized = False

    def init_device(self, filename: str) -> int:
        """
        :param filename: Pfad zur ddk-Datei als Python-String
        """
        language_c = c_short(1) # hat keine Bedeutung hier
        filename_c = filename.encode('utf-8')
        parent_c = c_void_p(0)  # hat keine Bedeutung hier
        wh_c = c_void_p(0)  # hat keine Bedeutung hier
        
        try:
            result = self.Device_Init(language_c, filename_c, parent_c, wh_c)
        except Exception as e:
            raise RuntimeError(f"Fehler beim Aufruf von Device_Init: {e}")
        match result:
            case 0:
                self.initialized = True
                print("Devices opened and instruments initialised")
            case 1:
                print("Wrong Parameter")
            case 2:
                print("File-Error in the Setup File")
            case x if 3 <= x <= 18:
                device = int((result-1)/2)
                if result % 2 == 0:
                    print("Wrong instrument type connected to Device ", device)
                else:
                    print("Error on opening Device ", device)
            case 19:
                print("No IBR-Instrument selected in the Setup")
            case 20:
                print("Error on loading the language")
            case 21:
                print("Error on loading the I/O-Catalogue [ IBR_IO.CAT not found ]")
            case 22:
                print("Error on loading the Universal Serial Driver [ IBR_DDK.USD not found ]")
            case -1:
                self.initialized = True
                result=0
                print("Device already initialized, continuing...")
        return result
            

    def get_version(self) -> tuple[int, int]:
        if self.initialized == False:
            print("called get_version, but device was not initialized")

        """
        Ruft die Geräteversion ab.
        return: Tuple mit Major- und Minor-Version (int, int)
        """
        ver_major = c_short()
        ver_minor = c_short()
        
        try:
            self.Device_GetVersion(byref(ver_major), byref(ver_minor))
            return ver_major.value, ver_minor.value
        except Exception as e:
            raise RuntimeError(f"Fehler beim Aufruf von Device_GetVersion: {e}")

    def get_value(self, devicenr: int, address: int) -> tuple[int, float]:
        if self.initialized == False:
            print("callled get_value, but device was not initialized")
        """
        Ruft einen Messwert von einem Taster ab.
        param devicenr: devicenr als short
        param address: adress als short (hier bin ich nicht sicher, wie die bei mehr als einer IBR vergeben werden)
        return: Tuple mit Status (short) und Messwert (double)
        """
        devicenr_c = c_short(devicenr)
        address_c = c_short(address)
        value = c_double()
        
        try:
            result = self.Device_Value(devicenr_c, address_c, byref(value))
            return result, value.value
        except Exception as e:
            raise RuntimeError(f"Fehler beim Aufruf von Device_Value: {e}")
            
    def deinit_device(self) -> int:
        """
        Deinitialisiert das Gerät und gibt die DLL-Ressourcen frei.
        :return: Rückgabewert der Funktion (short)
        """
        if not self.initialized:
            #print("Warnung: Gerät wurde nicht initialisiert, aber DeInit wird versucht.")
            return -1

        try:
            result = self.Device_DeInit()
            match result:
                case 0:
                    print("Device closed successfully.")
                case -1:
                    print("Device was not initialized")
                case _:
                    print("During DeInit there was an error on device ", deinit_result)
            self.initialized = False
            return result
        except Exception as e:
            raise RuntimeError(f"Fehler beim Aufruf von Device_DeInit: {e}")

    def __del__(self):
        """Automatische Deinitialisierung beim Löschen der Instanz."""
        if self.initialized:
            result = self.deinit_device()
            if result != 0:
                print(f"Fehler beim automatischen DeInit: Rückgabewert = {result}")
