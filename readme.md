# Wifi Test Script

A Python script that collects Wi-Fi connection and network performance information and stores the results in a CSV file.

It was specifically written for testing Wi-Fi from different physical locations and using different scenarios. This makes it possible to compare Wi-Fi performance when changing things such as access point configuration, placement, or other network conditions.

## Measurements

The script can collect the following measurements:

- Connected access point (BSSID)
- Signal strength
- Estimated RSSI
- Default gateway
- Gateway ping
- Internet ping
- Internet download speed
- Internet upload speed

Measurement groups can be enabled or disabled in `main()` as needed. All measurements are enabled by default except for default gateway information.

## Test Information

Before running the measurements, the script can prompt for:

- Test location
- Test scenario
- Additional remarks

This information is stored along with the measurements in the CSV file.

## Output

Test results are stored in a CSV file named:

```text
wifi_test_results.csv
```
