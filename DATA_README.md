# SmartNas performance — developer data pack

Built 2026-10-18 00:04. Companion to the "SmartNas Performance Benchmark" report.
Device: iPhone 15 Pro (A17 Pro, 6 cores, 8 GB), iOS 26.6.1. SmartNas 5.0.2 (App Store build), process name `Runner`.
Phone ran warm (40–43 °C) while charging and sharing hotspot.

## Sessions
| Session | What | Files |
|---|---|---|
| A · Launch runs | 27 cold launches (5 apps; per app 3 normal 5G + 2 very poor simulated; +2 3G for SmartNas), 25 s each, 500 ms sampling | data/launch_runs_*.csv |
| B · Free-use session | SmartNas, 8 min, 1 s sampling | data/session1_*.csv, logs/session1_errors.jsonl |
| C · Walkthrough | SmartNas, 10 min, 34 screen visits, 500 ms sampling | data/walkthrough_*.csv |
| D · eSIM purchase | SmartNas, paid try (ABA hand-off) | data/esim_*.csv, logs/esim_errors.jsonl |

## Metric definitions
- cpu_pct: sysmontap `cpuUsage`, percent of ONE core (max ~600% on 6 cores).
- footprint_mb: sysmontap `physFootprint` (what iOS jetsam limits use).
- disk_written: sysmontap `diskBytesWritten`, cumulative for the process.
- idle_cpu_median: median cpu_pct from t > 15 s to 25 s after launch, no touch input.
- Network sizes: bytes per process from pcapd packet tags; host names from DNS answers / TLS SNI. Payloads are encrypted.
- Simulated networks: Apple condition inducer SlowNetwork3GAverage, SlowNetworkVeryBadNetwork (1 Mbps, 500 ms, 10% loss).

## Using this with an AI assistant
Drop FOR_AI.md (and any CSV you care about) into the chat first. It explains every file, column and finding.

## Reproducing the tests
Follow REPRODUCE.md, or give it to an AI assistant that can run commands and let it walk you through.

## Not included (privacy)
- Raw network captures (.pcapng): contain all phone traffic, not only SmartNas.
- Any images or screenshots: screens show account details (ID card, face scan, eSIM QR/activation code, phone number, name, balance).
- Full logs: only ERROR/FAULT and error-like lines are included; emails, phone numbers, names, long numbers,
  device UDID and container paths are replaced with <tags>.

## Scripts
Python 3.13 + pymobiledevice3 11.34 (Windows). Need `pymobiledevice3 remote tunneld` running (admin) and Developer Mode.
Replace <your-device-udid>. startup_test.py: cold-launch test; walk_rec.py: screenshots-on-change + perf;
pcap_rec.py: per-process packet capture; analyze.py / per_screen.py / compare.py: summaries.
