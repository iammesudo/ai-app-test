# Context for an AI assistant: SmartNas performance data pack

You are helping an engineer analyse performance measurements of the iOS app **SmartNas 5.0.2** (Smart Axiata, Cambodia;
Flutter app, iOS process name `Runner`), compared with ABA Mobile 5.1.6, ACLEDA 6.2.98, Binance 3.21.5 and Taobao 10.66.40.
All data was captured on 2026-10-17 on ONE iPhone 15 Pro (A17 Pro, 6 CPU cores, 8 GB RAM, iOS 26.6.1) over USB with
Apple's developer instrumentation (pymobiledevice3). No jailbreak; apps were not modified; App Store builds (no symbols).
The phone was warm (40–43 °C) while charging and sharing hotspot, which can slow all apps slightly.
This pack contains no personal data and no images.

## Units and definitions (read first)
- `cpu_pct` / `cpu_pct_of_one_core`: percent of ONE core. 100 = one core fully busy. Max ≈ 600 on this phone. Not battery.
- `footprint_mb`: iOS physFootprint in MB (the value iOS uses to decide when to kill an app for memory).
- `disk_written_*`: bytes/MB written to storage by the process (cumulative counter).
- `up_kb` / `down_kb`: network bytes sent/received by the app process, in KB. Hosts come from DNS/TLS names; contents are encrypted.
- `idle_cpu_median_pct_t_gt_15s`: median CPU between 15 s and 25 s after launch with nobody touching the phone.
- Networks: `normal` = real 5G; `slow3g` and `verypoor` are SIMULATED by Apple's network conditioner
  (verypoor = 1 Mbps, 500 ms latency, 10% packet loss).
- "Ready time" (time until the home screen is usable) was read from screenshots and is NOT a column here; values are listed below.

## Sessions → files
| Session | Description | Files |
|---|---|---|
| A · Launch runs | 27 cold launches, 25 s each, 0.5 s sampling. Per app: 3 `normal` + 2 `verypoor`; SmartNas also 2 `slow3g`. Each run: force-kill, wait 4 s, launch. | `data/launch_runs_summary.csv` (one row per run), `data/launch_runs_samples.csv` (time series) |
| B · Free use | SmartNas only, 8 min, 1 s sampling. | `data/session1_timeline.csv`, `data/session1_hosts.csv`, `data/session1_log_patterns.csv`, `logs/session1_errors.jsonl` |
| C · Walkthrough | SmartNas only, 10 min, 34 screen visits across 29 distinct screens, 0.5 s sampling. | `data/walkthrough_perf.csv`, `data/walkthrough_screens.csv`, `data/walkthrough_screen_hosts.csv` |
| D · eSIM purchase | SmartNas only, one paid purchase handed off to ABA for payment. | `data/esim_steps.csv`, `data/esim_step_hosts.csv`, `logs/esim_errors.jsonl` |

## File schemas
- `launch_runs_summary.csv`: app, network, run, peak_cpu_pct, idle_cpu_median_pct_t_gt_15s, peak_footprint_mb, footprint_at_25s_mb, samples
- `launch_runs_samples.csv`: app, network, run, t_s (seconds after launch command), cpu_pct_of_one_core, footprint_mb
- `session1_timeline.csv`: t_s_from_first_log, cpu_pct, footprint_mb, threads, disk_written_mb_cumulative, disk_read_mb_cumulative
- `session1_hosts.csv`: host, up_kb, down_kb, first_seen, last_seen (clock time HH:MM:SS), ports
- `session1_log_patterns.csv`: pattern (normalised log message, digits → #), count
- `walkthrough_perf.csv`: t_s (from walkthrough start), cpu_pct, footprint_mb, disk_written_bytes_cumulative
- `walkthrough_screens.csv`: visit, screen, start_s, end_s, seconds, cpu_avg_pct, cpu_max_pct, footprint_max_mb, footprint_end_mb, disk_written_mb, up_kb, down_kb
- `walkthrough_screen_hosts.csv`: visit, screen, host, kb (top hosts per visit)
- `esim_steps.csv`: step, start_s, end_s, seconds, cpu_avg_pct, footprint_max_mb, up_kb, down_kb
- `logs/*.jsonl`: one JSON object per line: time, level, subsystem, category, image, message. Only ERROR/FAULT or error-like
  lines; personal details replaced by tags like <email>, <phone>, <name>, <number>, <device-udid>.

## Key findings (already computed; verify against the CSVs if asked)
| Measure | SmartNas | Others |
|---|---|---|
| Ready time, normal 5G (from screenshots) | 5.2 s | ABA 3.1, ACLEDA 2.2, Binance 3.0, Taobao 2.9 s |
| Ready time, very poor (simulated) | 25+ s (splash until server answers) | ABA/ACLEDA/Binance ≈ 2 s (show cached screen); Taobao stopped on a region prompt |
| Idle CPU median (normal) | 44.2% (runs 44.1–47.4) | ABA 0.5, ACLEDA 6.9, Binance 18.0, Taobao 31.8 |
| Footprint at 25 s (median) | 381 MB | ABA 244, ACLEDA 124, Binance 250, Taobao 275 |
| Peak CPU while opening | 186% (normal range) | 168–371% |
- Session B: 325 MB written to storage in 8 min (~40 MB/min overall; ~0.47 MB/s ≈ 28 MB/min while idle); 619 new TCP connections;
  321,970 log lines; ATTrackingManager status queried 1,197×; canOpenURL failed 380×; peak 73 threads; 0 crashes.
- Launch order (session B os_log): ATT check +53 ms, TikTok SDK +60 ms, Repro +84 ms, CLLocationManager +119 ms,
  Flutter engine +172 ms, Facebook/Firebase +207–214 ms; 9 hosts contacted in the first second.
- Session C: footprint grows ~410 → ~795 MB peak and stays ≥ ~620 MB after 5 min. Data by owner ≈ Smart 64%, Adjust 20%,
  ssnb.overseasbaas.com (unidentified) 9%, Google 4%, Facebook 1%. On Home, Adjust 427 KB vs Smart 27 KB in 54 s.
  Slow screens: History ~10 s loader; Switch account ~19 s loader after one tap; SmartRoam request failed 3 of 3.
- Session D (app-side waits only): device check 5–6 s with footprint up to ~890 MB; identity verification 4–13 s
  (face data to ekyc.bjrrtx.com and face.ap-southeast-2.myhuaweicloud.com); 24 s waiting after payment while the app
  polled the server ~8 times (~every 3 s).

## Re-running the tests
If the user wants to repeat the measurements, follow REPRODUCE.md in this pack (it has a section for AI assistants).

## How to answer common questions
- "How much slower is SmartNas?" → use the ready-time table above (ready time is not in the CSVs).
- "Is the idle CPU real?" → filter `launch_runs_samples.csv` to t_s > 15 and compare apps; see also `session1_timeline.csv`.
- "Which screen is heaviest?" → sort `walkthrough_screens.csv` by cpu_avg_pct or footprint_max_mb.
- "Where does the data go?" → group `walkthrough_screen_hosts.csv` by host owner (smart.com.kh = Smart; adjust = Adjust; etc.).

## Limits — do not overclaim
- One device, one day, warm phone. Treat seconds and percentages as ±10–15%; the ranking between apps is reliable.
- Battery was NOT measured; high idle CPU only suggests faster battery drain.
- Network payloads are encrypted: you can say where data went and how much, not what it contained.
- Other apps' network/tracker traffic was not captured, so tracker comparisons with other apps are not possible.
- Not covered: Android, older iPhones (3–4 GB RAM), per-endpoint server timings, code-level profiling.
