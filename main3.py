import sys
import time
import csv
import os
import logging
import re
from datetime import datetime
from statistics import mean
from ibrdll import IbrDll

# ------------------ Configuration ------------------

DLL_PATH = r"C:\IBR_DDK\DLL\Win32\ibr_ddk.dll"
SETUP_PATH = r"C:\IMB_Test\IMB_Test.ddk"
MODULE_NUMBER = 1
OUTPUT_DIR = "Measurements"
MIN_MEASUREMENT_INTERVAL = 0.13  # seconds, from empirical read time
MAX_OVERSAMPLE_COUNT = 50

DEFAULT_GAUGE_DESCRIPTIONS = {
    1: "Z direction 1",
    2: "Z direction 2",
    3: "Z direction 3",
    4: "X direction 1",
    5: "X direction 2",
    6: "Y direction",
}

# ------------------ Measurement Class ------------------

class MeasurementSession:
    def __init__(self, ibr, gauge_addresses, gauge_descriptions, frequency_hz, duration_hours, csv_filename):
        self.ibr = ibr
        self.gauge_addresses = gauge_addresses
        self.gauge_descriptions = gauge_descriptions
        self.frequency_hz = frequency_hz
        self.measurement_interval = 1 / frequency_hz
        self.duration_seconds = None if duration_hours is None else duration_hours * 3600
        self.oversample_count = min(int(self.measurement_interval / MIN_MEASUREMENT_INTERVAL), MAX_OVERSAMPLE_COUNT)
        self.csv_filename = csv_filename
        self.total_samples = 0

        self.csv_file = open(csv_filename, mode='w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow(["Timestamp"] +
                                 [gauge_descriptions.get(addr, f"Gauge {addr}") for addr in gauge_addresses])

    def read_gauge_value(self, module_number, gauge_number):
        status, value = self.ibr.get_value(module_number, gauge_number)
        if status != 0:
            if status == 136:
                logging.warning(f"Gauge #{gauge_number} ({self.gauge_descriptions.get(gauge_number)}) out of range")
            else:
                logging.error(f"Error {status} on gauge #{gauge_number} ({self.gauge_descriptions.get(gauge_number)})")
            return None
        return value

    def run(self):
        logging.info("Initializing device.")
        rc = self.ibr.init_device(SETUP_PATH)
        if rc != 0:
            logging.critical(f"Device initialization failed (rc={rc}).")
            sys.exit(1)


        start = time.time()
        deadline = None if self.duration_seconds is None else start + self.duration_seconds
        next_sample_time = time.monotonic()

        logging.info(f"Measurement started with {self.oversample_count}x oversampling.")
        try:
            while deadline is None or time.time() < deadline:
                now_local = datetime.now().astimezone().isoformat()
                row = [now_local]

                oversample_results = {addr: [] for addr in self.gauge_addresses}
                read_start = time.perf_counter()

                for _ in range(self.oversample_count):
                    for addr in self.gauge_addresses:
                        value = self.read_gauge_value(MODULE_NUMBER, addr)
                        if value is not None:
                            oversample_results[addr].append(value)
                        else:
                            oversample_results[addr].append(None)

                read_end = time.perf_counter()
                read_duration = read_end - read_start

                for addr in self.gauge_addresses:
                    samples = [v for v in oversample_results[addr] if v is not None]
                    avg_value = mean(samples) if samples else None

                    # Adaptive precision based on range of values
                    if samples and max(samples) - min(samples) < 1e-6:
                        fmt = "{:.8f}"
                    elif samples and max(samples) - min(samples) < 1e-5:
                        fmt = "{:.7f}"
                    elif samples and max(samples) - min(samples) < 1e-4:
                        fmt = "{:.6f}"
                    elif samples and max(samples) - min(samples) < 1e-3:
                        fmt = "{:.5f}"
                    elif samples and max(samples) - min(samples) < 1e-2:
                        fmt = "{:.4f}"
                    else:
                        fmt = "{:.3f}"

                    row.append(fmt.format(avg_value) if avg_value is not None else "error")

                self.csv_writer.writerow(row)
                self.csv_file.flush()
                self.total_samples += 1
                print(" | ".join(row))

                remaining = self.measurement_interval - read_duration
                if remaining > 0:
                    time.sleep(remaining)
                else:
                    logging.warning(f"Oversampling took longer than allowed interval ({read_duration:.3f}s > {self.measurement_interval:.3f}s)")

                next_sample_time += self.measurement_interval

        except KeyboardInterrupt:
            logging.warning("Measurement manually interrupted by user.")
            print("\nMeasurement interrupted.")
        except Exception as e:
            logging.exception(f"Unexpected error occurred: {e}")
            print(f"\nUnexpected error occurred: {e}")
        finally:
            self.finish()

    def finish(self):
        logging.info("Deinitializing device.")
        try:
            self.ibr.deinit_device()
        except Exception as e:
            logging.warning(f"Deinitialization failed: {e}")
        try:
            self.csv_file.close()
        except Exception as e:
            logging.warning(f"Failed to close CSV file: {e}")

        logging.info(f"Total samples collected: {self.total_samples}")
        print(f"Total samples: {self.total_samples}")

# ------------------ Sensor Selection Helpers ------------------

def parse_sensor_selection(selection: str, valid_sensors=None):
    """
    Parse a user sensor selection string, e.g.:
      - '4,5,6'
      - '1 4 6'
      - '1-3,6'
      - 'all' or '*'

    Returns a list of unique sensor numbers, preserving the user's order.
    """
    if valid_sensors is None:
        valid_sensors = set(DEFAULT_GAUGE_DESCRIPTIONS.keys())

    s = (selection or "").strip().lower()
    if not s:
        raise ValueError("Sensor selection cannot be empty.")

    if s in {"all", "*"}:
        return sorted(valid_sensors)

    tokens = re.split(r"[,\s]+", s)
    result = []
    seen = set()

    def _add_sensor(n: int):
        if n not in valid_sensors:
            raise ValueError(f"Invalid sensor #{n}. Valid sensors: {sorted(valid_sensors)}")
        if n not in seen:
            seen.add(n)
            result.append(n)

    for tok in tokens:
        if not tok:
            continue
        if "-" in tok:
            a, b = tok.split("-", 1)
            if not a or not b:
                raise ValueError(f"Invalid range token: '{tok}'")
            try:
                start = int(a)
                end = int(b)
            except ValueError:
                raise ValueError(f"Invalid range token: '{tok}'")
            step = 1 if start <= end else -1
            for n in range(start, end + step, step):
                _add_sensor(n)
        else:
            try:
                n = int(tok)
            except ValueError:
                raise ValueError(f"Invalid sensor token: '{tok}'")
            _add_sensor(n)

    if not result:
        raise ValueError("No valid sensors selected.")
    return result

# ------------------ Main Logic ------------------

def main():
    if not os.path.isfile(DLL_PATH):
        print(f"Missing DLL file: {DLL_PATH}")
        sys.exit(1)
    if not os.path.isfile(SETUP_PATH):
        print(f"Missing setup file: {SETUP_PATH}")
        sys.exit(1)

    try:
        sensor_sel = input(
            "Enter sensor addresses to use (1–6). Examples: 4,5,6 | 1 4 6 | 1-3,6 | 'all'\n"
            "Leave blank to select by count (first N sensors): "
        ).strip()

        if sensor_sel:
            gauge_addresses = parse_sensor_selection(sensor_sel)
        else:
            num_sensors = int(input("Enter number of sensors to use (1–6): "))
            if not 1 <= num_sensors <= 6:
                raise ValueError("Sensor count must be between 1 and 6.")
            gauge_addresses = list(DEFAULT_GAUGE_DESCRIPTIONS.keys())[:num_sensors]


        freq_input = input("Enter frequency in Hz (0.001–100): ").strip()
        frequency_hz = float(freq_input)
        if not 0.001 <= frequency_hz <= 100:
            raise ValueError("Frequency must be between 0.001 and 100 Hz.")

        measurement_interval = 1 / frequency_hz
        min_interval_needed = MIN_MEASUREMENT_INTERVAL
        if measurement_interval < min_interval_needed:
            raise ValueError(f"Frequency too high. Minimum interval must be ≥ {min_interval_needed:.3f} s")

        duration_input = input("Enter duration in hours (leave blank for no time limit): ").strip()
        duration_hours = float(duration_input) if duration_input else None

        custom_names = input("Do you want to enter custom names for the sensors? (y/n): ").strip().lower()
        if custom_names == 'y':
            gauge_descriptions = {}
            for addr in gauge_addresses:
                name = input(f"Enter name for sensor address {addr}: ").strip()
                gauge_descriptions[addr] = name if name else f"Gauge {addr}"
        else:
            gauge_descriptions = {addr: DEFAULT_GAUGE_DESCRIPTIONS[addr] for addr in gauge_addresses}

    except ValueError as e:
        print(f"Invalid input: {e}")
        sys.exit(1)

    timestamp = datetime.now().strftime('%Y-%m-%dT%H-%M-%S')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    csv_filename = os.path.join(OUTPUT_DIR, f"measurement_{timestamp}.csv")
    log_filename = os.path.join(OUTPUT_DIR, f"measurement_{timestamp}.log")

    logging.basicConfig(
        filename=log_filename,
        filemode='a',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    logging.info("----- Measurement Configuration -----")
    logging.info(f"Gauge addresses: {gauge_addresses}")
    logging.info(f"Gauge descriptions: {gauge_descriptions}")
    logging.info(f"Frequency: {frequency_hz} Hz")
    logging.info(f"Duration (hours): {'infinite' if duration_hours is None else duration_hours}")
    logging.info("-------------------------------------")
    session = MeasurementSession(
        ibr=IbrDll(DLL_PATH),
        gauge_addresses=gauge_addresses,
        gauge_descriptions=gauge_descriptions,
        frequency_hz=frequency_hz,
        duration_hours=duration_hours,
        csv_filename=csv_filename
    )
    session.run()

if __name__ == "__main__":
    main()
