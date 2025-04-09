# IBR_Controller
A controller software for control and read-out of TESA gauges using an IBR bus. The Python script wraps a C++ library supplied by the IBR.


Theoretical values in the setup file for measurements. At the end, can be taken from IBR Test and does not have to be touched by developer.

Setup file
Address: 0:  2 Device type
Address: 2:  0
Address: 4: 301 Instrument type
Address: 17: 0
Address: 32: 68 Module type

Offset 0 (2 bytes): Device type
Offset 2 (2 bytes): Device address
Offset 4 (2 bytes): Instrument type
Offset 6 (1 byte out of the 24 for COM/USB or IMB-lan serial)
Offset 30 (2 bytes): For “Connection 1 [ADR1.1]” → Connection state (for IBRit-mc, etc.)
Offset 32 (1 byte): If it’s IMBus, this is the “module type.” If it’s an IBRit, it might be used differently.
Offset 33 (1 byte): IMBus channel number or other usage.
Offset 34 (2 bytes): “High-Master” in many instruments.
Offset 36 (2 bytes): “Low-Master.”
Offset 38 (2 bytes): “Master for Zero Adjustment.”
Offset 40 (4 bytes): “Zero offset” (float).
Offset 44 (2 bytes): Possibly “Reserved” or digital step, depending on instrument.
