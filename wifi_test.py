"""
Wifi Test Script

A script that collects Wi-Fi speed and connection info and store the data to a csv file. It was specifcally written for testing WI-FI from different locations and using scenarios.

Measurements include
- Connected access point (BSSID)
- Signal strength
- Estimated RSSI
- Default gateway
- Gateway ping
- Internet ping
- Internet speed test.

Measurement groups can be enabled or disabled in `main()` as needed. All are enabled by default.

This script is intended for Windows systems and relies on Windows networking utilities such as `netsh`, `ipconfig`, and `ping`. Internet speed testing requires the `speedtest-cli` package, and LAN throughput testing requires `iperf3`.

Written by RandomGgames along with Google Gemini and OpenAI's ChatGPT.
"""

from datetime import datetime
from pathlib import Path
import csv
import json
import logging
import re
import subprocess
import sys

import speedtest

__version__ = "1.0.0"  # Major.Minor.Patch

logger = logging.getLogger(__name__)


def get_wifi_details():
    """Returns Wi-Fi signal percentage, estimated RSSI, and BSSID."""
    try:
        output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], text=True, stderr=subprocess.STDOUT)

        bssid_match = re.search(r"BSSID\s*:\s*([0-9a-fA-F:]+)", output)
        signal_match = re.search(r"Signal\s*:\s*(\d+)%", output)

        bssid = bssid_match.group(1) if bssid_match else None

        if signal_match:
            signal = int(signal_match.group(1))

            if signal <= 0:
                rssi = -100
            elif signal >= 100:
                rssi = -50
            else:
                rssi = int((signal / 2) - 100)
        else:
            signal = None
            rssi = None

        return bssid, signal, rssi

    except Exception as e:
        logger.debug("Failed to get Wi-Fi details: %s", e)
        return None, None, None


def get_default_gateway():
    """Returns the IPv4 default gateway."""
    try:
        output = subprocess.check_output(["ipconfig"], text=True, stderr=subprocess.STDOUT)

        matches = re.findall(r"Default Gateway[ .]*:\s*([0-9.]+)", output)

        for gateway in matches:
            if gateway:
                return gateway

        return None

    except Exception as e:
        logger.debug("Failed to get default gateway: %s", e)
        return None


def ping_host(host, count=4):
    """Pings a host and returns min, average, and max latency in milliseconds."""
    try:
        output = subprocess.check_output(["ping", "-n", str(count), host], text=True, stderr=subprocess.STDOUT)

        match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)

        if match:
            minimum = float(match.group(1))
            maximum = float(match.group(2))
            average = float(match.group(3))
            return minimum, average, maximum

        return None, None, None

    except Exception as e:
        logger.debug("Ping failed for %s: %s", host, e)
        return None, None, None


def run_internet_speed_test():
    """Performs an Internet download/upload speed test."""
    logger.debug("Running Internet speed test (this may take a moment)...")

    try:
        st = speedtest.Speedtest()
        st.get_best_server()

        download_speed = round(st.download() / 1_000_000, 2)
        upload_speed = round(st.upload() / 1_000_000, 2)

        return download_speed, upload_speed

    except Exception as e:
        logger.debug("Internet speed test failed: %s", e)
        return None, None


def run_lan_speed_test(server, duration=10):
    """Runs an iperf3 LAN throughput test against the specified server."""
    logger.debug("Running LAN speed test against %s...", server)

    try:
        output = subprocess.check_output(["iperf3", "-c", server, "-t", str(duration), "-J"], text=True, stderr=subprocess.STDOUT)

        data = json.loads(output)

        bits_per_second = data["end"]["sum_received"]["bits_per_second"]
        download_speed = bits_per_second / 1_000_000

        return download_speed

    except FileNotFoundError:
        logger.debug("iperf3 was not found.")
        return None

    except Exception as e:
        logger.debug("LAN speed test failed: %s", e)
        return None


def save_test_result(test_result, filename: Path = Path("tests.csv")):
    file_exists = filename.is_file()

    fieldnames = [
        "Timestamp",
        "Location",
        "Scenario",
        "Remarks",
        "BSSID",
        "Signal %",
        "RSSI Est.",
        "Gateway",
        "Gateway Ping Min (ms)",
        "Gateway Ping Max (ms)",
        "Gateway Ping Avg (ms)",
        "Internet Ping Min (ms)",
        "Internet Ping Max (ms)",
        "Internet Ping Avg (ms)",
        "Download (Mbps)",
        "Upload (Mbps)"
    ]

    with filename.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(test_result)


def main():
    log_test_info = True
    log_wifi_details = True
    log_gateway_details = False
    measure_gateway_ping = True
    measure_internet_ping = True
    perform_speed_test = True
    filepath = Path(r"wifi_test_results.csv")

    location = None
    scenario = None
    remarks = None

    bssid = None
    signal = None
    rssi = None

    gateway = None
    gateway_ping_min = None
    gateway_ping_avg = None
    gateway_ping_max = None

    internet_ping_min = None
    internet_ping_avg = None
    internet_ping_max = None

    download_speed = None
    upload_speed = None

    if log_test_info:
        location = input("Describe test location: ")
        scenario = input("Describe test scenario: ")
        remarks = input("Describe any other test remarks: ")

        logger.debug("Location: %s", location)
        logger.debug("Scenario: %s", scenario)
        logger.debug("Remarks: %s", remarks)

    if log_wifi_details:
        bssid, signal, rssi = get_wifi_details()
        logger.debug("BSSID: %s", bssid)
        logger.debug("Signal: %s%%", signal)
        logger.debug("Estimated RSSI: %s", rssi)

    if log_gateway_details or measure_gateway_ping:
        gateway = get_default_gateway()
        if log_gateway_details:
            logger.debug("Gateway: %s", gateway)
        if measure_gateway_ping:
            gateway_ping_min, gateway_ping_avg, gateway_ping_max = ping_host(gateway) if gateway else (None, None, None)
            logger.debug("Gateway ping min: %s ms", gateway_ping_min)
            logger.debug("Gateway ping max: %s ms", gateway_ping_max)
            logger.debug("Gateway ping average: %s ms", gateway_ping_avg)

    if measure_internet_ping:
        internet_ping_min, internet_ping_avg, internet_ping_max = ping_host("1.1.1.1")
        logger.debug("Internet ping min: %s ms", internet_ping_min)
        logger.debug("Internet ping max: %s ms", internet_ping_max)
        logger.debug("Internet ping average: %s ms", internet_ping_avg)

    if perform_speed_test:
        download_speed, upload_speed = run_internet_speed_test()
        logger.debug("Download Speed: %s Mbps", download_speed)
        logger.debug("Upload Speed: %s Mbps", upload_speed)

    test_result = {
        "Timestamp": datetime.now().isoformat(timespec="seconds"),
        "Location": location,
        "Scenario": scenario,
        "Remarks": remarks,
        "BSSID": bssid,
        "Signal %": signal,
        "RSSI Est.": rssi,
        "Gateway": gateway,
        "Gateway Ping Min (ms)": gateway_ping_min,
        "Gateway Ping Max (ms)": gateway_ping_max,
        "Gateway Ping Avg (ms)": gateway_ping_avg,
        "Internet Ping Min (ms)": internet_ping_min,
        "Internet Ping Max (ms)": internet_ping_max,
        "Internet Ping Avg (ms)": internet_ping_avg,
        "Download (Mbps)": download_speed,
        "Upload (Mbps)": upload_speed
    }

    save_test_result(test_result, filename=filepath)


class JsonArgsFilter(logging.Filter):
    """Format strings and Paths as JSON strings in log arguments."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not record.args:
            return True

        args = record.args if isinstance(record.args, tuple) else (record.args,)
        processed = []

        for value in args:
            if isinstance(value, Path):
                processed.append(json.dumps(value.as_posix()))
            elif isinstance(value, str):
                processed.append(json.dumps(value))
            elif isinstance(value, (int, float, bool)) or value is None:
                processed.append(value)
            else:
                processed.append(json.dumps(value, default=str))

        record.args = tuple(processed)
        return True


def enforce_max_log_count(log_dir: Path, max_log_files: int = 30) -> None:
    """Remove old log files when the maximum log count is exceeded."""
    if max_log_files <= 0:
        return

    script_name = Path(__file__).stem
    log_files = sorted(log_dir.glob(f"*__{script_name}.log"))

    for log_file in log_files[:-max_log_files]:
        try:
            log_file.unlink()
        except OSError as e:
            logger.debug("Failed removing old log %s: %s", log_file, e)


def setup_logging() -> Path:
    """Set up console and per-run file logging and return the log path."""
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addFilter(JsonArgsFilter())

    log_dir = Path(__file__).resolve().parent / "Logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_name = Path(__file__).stem
    log_path = log_dir / f"{timestamp}__{script_name}.log"

    formatter = logging.Formatter("%(asctime)s.%(msecs)03d [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S",)

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    enforce_max_log_count(log_dir)

    return log_path


def bootstrap() -> int:
    """Set up the script, run main(), and handle unexpected errors."""
    exit_code = 0

    try:
        setup_logging()
        main()
    except KeyboardInterrupt:
        logger.warning("Operation interrupted by user.")
        exit_code = 130
    except Exception as e:
        logger.exception("A fatal error has occurred: %s", e)
        exit_code = 1

    if exit_code != 0:
        input("Press Enter to exit...")
    # input("Press Enter to exit...")

    return exit_code


if __name__ == "__main__":
    sys.exit(bootstrap())
