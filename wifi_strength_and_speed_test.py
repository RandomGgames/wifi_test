"""
{Script Name}

{Summary of what the script does}

{How to use the script}
"""

from datetime import datetime
from pathlib import Path
import json
import logging
import os
import re
import subprocess
import sys

import speedtest

__version__ = "0.0.0"  # Major.Minor.Patch

logger = logging.getLogger(__name__)


def get_wifi_signal():
    """Gets the current Wi-Fi signal strength as a percentage."""
    # logger.debug("Checking Wi-Fi signal strength...")
    try:
        # Runs the Windows native tool to check wireless info
        output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('utf-8')

        # Searches for the 'Signal' line in the output
        match = re.search(r"Signal\s*:\s*(\d+)%", output)
        if match:
            return f"{match.group(1)}%"
        return "Unknown (Are you connected to Wi-Fi?)"
    except Exception:
        return "Error reading Wi-Fi signal."


def run_speed_test():
    """Performs a generic download and upload speed test."""
    logger.debug("Running speed test (this may take a moment)...")
    try:
        # Connects to the closest speedtest.net server
        st = speedtest.Speedtest()
        st.get_best_server()

        # Convert speeds from bits per second to Megabits per second (Mbps)
        download_speed = st.download() / 1_000_000
        upload_speed = st.upload() / 1_000_000
        ping = st.results.ping

        return download_speed, upload_speed, ping
    except Exception as e:
        logger.debug("Speed test failed: %s", e)
        return None, None, None


def get_windows_rssi():
    """Converts the Windows Wi-Fi quality percentage to a dBm RSSI value."""
    # logger.debug("Checking Wi-Fi RSSI...")
    try:
        output = subprocess.check_output("netsh wlan show interfaces", shell=True).decode('utf-8')
        match = re.search(r"Signal\s*:\s*(\d+)%", output)

        if match:
            quality = int(match.group(1))
            # Standard formula to map 0-100% quality to roughly -100 to -50 dBm
            if quality <= 0:
                rssi = -100
            elif quality >= 100:
                rssi = -50
            else:
                rssi = (quality / 2) - 100
            return f"{int(rssi)} dBm"
        return "Unknown (Are you connected to Wi-Fi?)"
    except Exception:
        return "Error reading Wi-Fi status."


def main():
    location = input("What is your current location?\n>>> ")
    logger.debug("Testing WIFI at %s", location)
    signal = get_wifi_signal()
    logger.debug("[Wi-Fi Status] Signal Strength: %s", signal)

    rssi_val = get_windows_rssi()
    logger.debug("[Wi-Fi Status] RSSI: %s", rssi_val)

    # 2. Run Speed Test
    dl, ul, png = run_speed_test()
    if dl:
        logger.debug("[Speed Test] Download: %.2f Mbps", dl)
        logger.debug("[Speed Test] Upload:   %.2f Mbps", ul)
        logger.debug("[Speed Test] Ping:     %.2f ms", png)


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
