> Windows guide. On a Mac, follow MAC_GUIDE.md instead; the steps are the same but the commands differ.

# How to reproduce the SmartNas performance results

This guide repeats the tests behind the "SmartNas Performance Benchmark" report. You can follow it yourself,
or give this file to an AI assistant that can run commands on your computer and let it do the steps with you.

Three ways to prove the findings:
- **A. Same method as the report.** A Windows laptop plus an iPhone over USB. No Mac, no jailbreak, no app changes.
- **B. Xcode Instruments on your own build.** The strongest proof, because it shows which code causes each problem.
- **C. Backend proof.** Look up the slow or failed requests in the server logs at the times listed below.

---

## If you are an AI assistant following this guide

- Work through Part A in order. Run one step at a time and check its "Expected result" before moving on.
- Ask the human before any step that needs them: unlocking or touching the phone, tapping **Trust**, turning on
  Developer Mode, approving the Windows admin prompt, or tapping through the app during the walkthrough.
- Never type passwords, PINs or payment details. During launch tests the human must **not** touch the phone.
- Always run the "clear network condition" command after a slow-network test, even if a step failed.
- Treat `out/` recordings as private: network captures include all phone traffic, and screenshots can show
  account details. Don't upload or paste them anywhere.
- Report results in the same units as the report: CPU % of one core, footprint in MB, seconds to ready.

---

## What you need

- An iPhone with the apps installed and logged in, plus a USB cable.
- A Windows laptop with Apple Mobile Device support (the iTunes or Apple Devices app).
- **Python 3.13.** Python 3.14 fails to build one dependency.
- Admin rights on the laptop, for the USB tunnel.
- The `scripts/` folder from this pack.
- About 10 minutes per app for launch tests, and about 15 minutes for a walkthrough.

## Keep the test fair

- Phone **below 35 °C**: hotspot off, not fast-charging, out of its case.
  Check with `py -3.13 -m pymobiledevice3 diagnostics battery single` (Temperature ÷ 100 = °C).
- Same phone, same network and same day for every app you compare.
- Screen unlocked with auto-lock off. Close other apps before starting.

---

## Part A — Same method as the report

Replace `<UDID>` with your phone's ID (step 2). Run commands from the folder that contains `scripts/`.

### Step 1 — Install the tool
```
py -3.13 -m pip install pymobiledevice3
```
**Expected result:** the install finishes without errors. If `py -3.13` isn't found, install Python 3.13 first.

### Step 2 — Connect the phone and get its ID
Plug in the phone, unlock it, and tap **Trust** on the phone.
```
py -3.13 -m pymobiledevice3 lockdown info
```
**Expected result:** JSON output. Copy the `UniqueDeviceID` value; that's your `<UDID>`.
Also put it in the line `UDID = "<your-device-udid>"` at the top of `scripts/startup_test.py` and `scripts/walk_rec.py`.

### Step 3 — Turn on Developer Mode
```
py -3.13 -m pymobiledevice3 amfi reveal-developer-mode
```
On the phone: Settings → Privacy & Security → **Developer Mode** (at the bottom) → On → Restart → Turn On.
```
py -3.13 -m pymobiledevice3 amfi developer-mode-status
```
**Expected result:** it prints `true`.

### Step 4 — Start the USB tunnel (keep it open)
In a terminal opened **as Administrator**, start this and leave it running for the whole test:
```
py -3.13 -m pymobiledevice3 remote tunneld
```
In a normal terminal, load Apple's developer image (once per phone restart):
```
py -3.13 -m pymobiledevice3 mounter auto-mount --tunnel <UDID>
```
**Expected result:** opening `http://127.0.0.1:49151/` in a browser lists your UDID (not `{}`), and the mount
says "mounted successfully" or "already mounted".

### Step 5 — App IDs used in the report
```
py -3.13 -m pymobiledevice3 apps list -t User > apps.json
```
| App | Bundle ID | Process name |
|---|---|---|
| SmartNas | `smartnas` | `Runner` |
| ABA Mobile | `com.paygo24.ababank` | `ababank` |
| ACLEDA | `com.domain.acledabankqr` | `ToanChet` |
| Binance | `com.czzhao.binance` | `Binance` |
| Taobao | `com.taobao.taobao4iphone` | `Taobao4iPhone` |

The process name is `CFBundleExecutable` in `apps.json`.

### Step 6 — Launch test, normal network
This runs 3 cold launches of 25 s each. For each one the script force-closes the app, waits 4 s, launches it,
then saves a screenshot about every 0.5 s along with CPU and memory. **Don't touch the phone.**
```
py -3.13 scripts/startup_test.py out/smartnas-normal 3 - smartnas Runner
```
Repeat for each app with its bundle ID and process name (e.g. `... out/aba-normal 3 - com.paygo24.ababank ababank`).
**Expected result:** it prints `run 1: N screenshots, M perf samples` for each run, and `out/<name>/results.json` plus
`run1_…jpg` frames are created. A harmless `feed_data after feed_eof` error may appear at the end.
**Ready time** = the first frame where real data appears (for SmartNas: the balance, ~5.2 s in the report).

### Step 7 — Launch test, very poor network (simulated)
```
py -3.13 scripts/startup_test.py out/smartnas-verypoor 2 SlowNetworkVeryBadNetwork smartnas Runner
```
Other profiles are `SlowNetwork3GAverage` and `SlowNetworkEdgeAverage`. List them all with:
```
py -3.13 -m pymobiledevice3 developer dvt condition list --tunnel <UDID>
```
**Always clear the condition afterwards**, or the phone stays slow:
```
py -3.13 -m pymobiledevice3 developer dvt condition clear --tunnel <UDID>
```
**Expected result:** SmartNas shows the splash for about 15 s and needs 25 s or more to show the balance, while
ABA, ACLEDA and Binance show their home screen in about 2 s.

### Step 8 — Walkthrough: screens, CPU/memory and network
Start both recorders, each in its own terminal, then the human taps through the app:
```
py -3.13 scripts/walk_rec.py out/walk
```
```
py -3.13 scripts/pcap_rec.py <UDID> out/walk/network.pcapng
```
To stop both cleanly, create an empty file named `STOP` in `out/walk`:
```
type nul > out\walk\STOP
```
Then name the screens by looking at the saved frames, and write `out/walk/segments.json` as
`[[first_frame_index, last_frame_index, "Screen name"], ...]`. Frame indexes are positions in the `shots` list
of `walk.json`.
**Expected result:** `walk.json`, `.jpg` frames and `network.pcapng` in `out/walk`. The capture contains the
**whole phone's** traffic, so keep it private.

### Step 9 — Free-use session: logs, storage, connections
Run these three, each in its own terminal, and use the app normally for about 8 minutes:
```
py -3.13 -m pymobiledevice3 developer dvt sysmon process monitor process -f name=Runner --choose first --keep-monitoring -i 1000 --output out/s1/perf.jsonl --tunnel <UDID>
```
```
py -3.13 -m pymobiledevice3 syslog live -pn Runner --format json -o out/s1/app-log.jsonl --udid <UDID>
```
```
py -3.13 scripts/pcap_rec.py <UDID> out/s1/network.pcapng
```
Stop the first two with Ctrl+C, and the capture with a `STOP` file in `out/s1`.

### Step 10 — Turn recordings into numbers
```
py -3.13 scripts/analyze.py out/s1 Runner
```
→ `out/s1/summary.json`: CPU, memory and disk totals, servers by data, and log patterns.
```
py -3.13 scripts/per_screen.py out/walk out/walk/segments.json
```
→ `out/walk/per_screen.json`: CPU, memory, disk and servers for each screen visit.
```
py -3.13 scripts/compare.py out smartnas-normal smartnas-verypoor
```
→ peak CPU, idle CPU (median after 15 s) and memory per run, plus a contact sheet of frames.

**Compare with the report** (from `data/launch_runs_summary.csv` in this pack): SmartNas idle CPU ≈ 44% vs ABA ≈ 0.5%;
footprint at 25 s ≈ 381 MB vs 124–275 MB for the others. Expect ±10–15%, more if the phone is warmer or cooler.

### Problems we hit, and fixes
| Symptom | Fix |
|---|---|
| pip fails building `pylzss` | Use Python 3.13, not 3.14 |
| Developer Mode missing in Settings | Run `amfi reveal-developer-mode` with the phone connected, then reopen Settings |
| "Device is not connected" for syslog or pcap | Use `--udid <UDID>` for syslog and pcap; use `--tunnel <UDID>` for sysmon, screenshots, launch and conditions |
| `--tunnel` says it requires an argument (PowerShell) | Pass the UDID, not an empty string |
| Network capture file stays at 0 bytes | Only one capture can run at a time. Close any older capture process, wait ~30 s, start again |
| Huge capture file | Screenshots travel over the same USB link. Filter by process, as `analyze.py` does |
| Headless browser can't save to a folder with `'` in its name | Save to a temp folder, then copy |
| A banking app shows a security warning | Some apps react to Developer Mode. Note it and skip that app |
| Numbers slower than the report | Check phone temperature (see "Keep the test fair") |

---

## Part B — Xcode Instruments on your own build (needs a Mac)

With your own build you get symbols, so Instruments shows **which functions and widgets** cause each problem.
1. Build in profile mode: `flutter build ios --profile`, then open the project in Xcode.
2. Xcode → Product → **Profile** → choose a template:

| Finding to confirm | Instruments template | What to look for |
|---|---|---|
| Slow launch, partner SDKs before first frame | App Launch | Time to first frame; SDK init on the main thread |
| ~44% CPU on a still Home screen | Time Profiler | Heaviest stack while idle (animation tickers, timers, streams) |
| Memory growth to ~800 MB | Allocations + Leaks | Image cache and web/map views that persist after leaving screens |
| 325 MB written in 8 minutes | File Activity | Which files are written over and over |
| Battery impact | Energy Log | Energy impact on Home at rest, compared with ABA |

Flutter DevTools (performance tab, "Track widget rebuilds") shows which widgets redraw on the idle Home screen.

---

## Part C — Backend proof

The app's traffic is encrypted, so request details live on the server. Look up these times
(17 Oct 2026, Cambodia time, UTC+7):

| What | When | Host | Expected in logs |
|---|---|---|---|
| SmartRoam on/off failed ×3 | 19:23:40, 19:23:43, 19:23:52 | prod-bff-smartnas.smart.com.kh | 3 error responses for the roaming endpoint |
| Switch account ~19 s | 19:25:37 → 19:25:56 | prod-bff-smartnas.smart.com.kh, ssnb.overseasbaas.com | Slow profile/account calls |
| History ~10 s | 19:20:28 → 19:20:38 | prod-bff-smartnas.smart.com.kh | Slow balance-history response |
| Payment status polled ×8 | 20:07:03 → 20:07:27 | app-assets.smart.com.kh | 8 status polls about every 3 s, none returning "paid" |
| eKYC verify ~13 s | 20:06:21 → 20:06:34 | ekyc.bjrrtx.com, Huawei Cloud face API | Vendor response time |

Keep this table inside the team, because it describes one account's activity.
