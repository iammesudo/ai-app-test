# Mac guide: set up and run the tests

> **Status: not yet proven on a Mac.** These steps are translated from a Windows run (`REPRODUCE.md`). The tool and scripts are
> cross-platform, so it should work, but expect a snag or two. If a step fails, paste the error to Claude. It will fix it and update this file.

You can do this with Claude (say "Set up and check that the phone is connected") or by hand with the commands below.
Every step shows the result you should see before you move on.

## What you need
- A Mac with Xcode (or at least the Command Line Tools) and an iPhone with iOS 17 or newer, plus a USB cable.
- Your admin password (the USB tunnel needs `sudo`).
- About 30 minutes the first time.

## Part 1: One-time setup

### 1. Python 3.13 and the tool
Python 3.14 fails to build one dependency, so use 3.13.
```
brew install python@3.13
python3.13 -m venv .venv
source .venv/bin/activate
pip install "pymobiledevice3==11.34.0" pillow
```
**Expected result:** the install ends without errors. `pymobiledevice3 version` prints a version number.
Open a new terminal later? Run `source .venv/bin/activate` again inside this folder.

### 2. Connect the phone and get its ID
Plug in the phone, unlock it, tap **Trust** on the phone.
```
pymobiledevice3 usbmux list
```
**Expected result:** a list with your phone. Copy its `Identifier` (the UDID), then set it for this terminal:
```
export UDID=<paste-the-id-here>
```

### 3. Turn on Developer Mode (once per phone)
```
pymobiledevice3 amfi reveal-developer-mode
```
On the phone: Settings, Privacy & Security, **Developer Mode** (at the bottom), On, Restart, Turn On. Then:
```
pymobiledevice3 amfi developer-mode-status
```
**Expected result:** `true`.

### 4. Start the USB tunnel (keep it open the whole time)
In a **second terminal window**, in this folder:
```
source .venv/bin/activate
sudo "$(which python)" -m pymobiledevice3 remote tunneld
```
Type your Mac password when asked. Leave this window open.
Back in the first window, load Apple's developer image (once per phone restart):
```
pymobiledevice3 mounter auto-mount --tunnel $UDID
```
**Expected result:** opening `http://127.0.0.1:49151/` in a browser lists your phone (not `{}`), and the mount says
"mounted successfully" or "already mounted".

### 5. App IDs
```
pymobiledevice3 apps list -t User > apps.json
```
| App | Bundle ID | Process name |
|---|---|---|
| SmartNas | `smartnas` | `Runner` |
| ABA Mobile | `com.paygo24.ababank` | `ababank` |
| ACLEDA | `com.domain.acledabankqr` | `ToanChet` |
| Binance | `com.czzhao.binance` | `Binance` |
| Taobao | `com.taobao.taobao4iphone` | `Taobao4iPhone` |

For any other app: find its bundle ID in `apps.json`. The process name is `CFBundleExecutable` in the same entry.

## Part 2: Run the tests

Run all of these from this folder, with the virtual environment active and `UDID` set.
Check the phone is cool first (below 35 C): `pymobiledevice3 diagnostics battery single` (Temperature divided by 100 is degrees C).

### 6. Launch test, normal network (do not touch the phone)
```
python scripts/startup_test.py out/smartnas-normal 3 - smartnas Runner
```
It force-closes the app, waits 4 s, launches it, and saves a screenshot about every 0.5 s with CPU and memory, 3 times.
**Expected result:** `run 1: N screenshots, M perf samples` for each run, and `out/smartnas-normal/results.json` plus `run1_...jpg` frames.
A harmless `feed_data after feed_eof` message may appear at the end.
**Time to ready** is the first frame where real data shows (for SmartNas: the balance, about 5.2 s in the report).

### 7. Launch test, very poor network (simulated)
```
python scripts/startup_test.py out/smartnas-verypoor 2 SlowNetworkVeryBadNetwork smartnas Runner
```
Other profiles: `SlowNetwork3GAverage`, `SlowNetworkEdgeAverage`. List all: `pymobiledevice3 developer dvt condition list --tunnel $UDID`.
**Always clear it afterwards**, or the phone stays slow:
```
pymobiledevice3 developer dvt condition clear --tunnel $UDID
```

### 8. Walkthrough: screens, CPU, memory, network
Use two terminals (both with the venv active and `UDID` set). Start both, then tap through the app yourself:
```
python scripts/walk_rec.py out/walk
```
```
python scripts/pcap_rec.py $UDID out/walk/network.pcapng
```
To stop both cleanly:
```
touch out/walk/STOP
```
Then name the screens by looking at the saved frames and write `out/walk/segments.json` as
`[[first_frame_index, last_frame_index, "Screen name"], ...]`. Claude can do this from the frames if you ask.
**Expected result:** `walk.json`, `.jpg` frames and `network.pcapng` in `out/walk`. The capture holds the whole phone's traffic: keep it private.

### 9. Free-use session: logs, storage, connections
Three terminals, then use the app normally for about 8 minutes:
```
pymobiledevice3 developer dvt sysmon process monitor process -f name=Runner --choose first --keep-monitoring -i 1000 --output out/s1/perf.jsonl --tunnel $UDID
```
```
pymobiledevice3 syslog live -pn Runner --format json -o out/s1/app-log.jsonl --udid $UDID
```
```
python scripts/pcap_rec.py $UDID out/s1/network.pcapng
```
Stop the first two with Ctrl+C and the capture with `touch out/s1/STOP`.

### 10. Turn recordings into numbers
```
python scripts/analyze.py out/s1 Runner
python scripts/per_screen.py out/walk out/walk/segments.json
python scripts/compare.py out smartnas-normal smartnas-verypoor
```
These write `summary.json`, `per_screen.json` and a comparison of peak CPU, idle CPU (median after 15 s) and memory per run.
**Compare with the SmartNas report** (`data/launch_runs_summary.csv`): idle CPU about 44% vs ABA about 0.5%; memory at 25 s about 381 MB vs 124 to 275 MB.
Expect plus or minus 10 to 15 percent, more if the phone is warmer or cooler.

## Part 3: Prove a finding in code (needs your own build)
With your own build you get symbols, so Xcode Instruments shows which functions cause each problem.
See `REPRODUCE.md`, Part B (App Launch, Time Profiler, Allocations, File Activity, Energy Log).

## Differences from Windows
| Windows | Mac |
|---|---|
| `py -3.13 -m pymobiledevice3 ...` | `pymobiledevice3 ...` (venv active) |
| Admin terminal for `tunneld` | `sudo` for `tunneld` |
| `type nul > out\walk\STOP` | `touch out/walk/STOP` |
| UDID typed into scripts | `export UDID=...` |

## If this happens, do this
| Symptom | Fix |
|---|---|
| Phone not listed | Unplug, replug, unlock, tap Trust again, then retry |
| `tunneld` says permission denied | Run it with `sudo` using the venv's python, as in step 4 |
| `http://127.0.0.1:49151/` shows `{}` | The tunnel can't see the phone. Check Trust and that the phone is unlocked, restart `tunneld` |
| Developer Mode missing in Settings | Run `amfi reveal-developer-mode` with the phone connected, then reopen Settings |
| "Device is not connected" for syslog or pcap | Use `--udid $UDID` for syslog and pcap; `--tunnel $UDID` for the others |
| pip fails building `pylzss` | You are on Python 3.14. Use 3.13 |
| Capture file stays at 0 bytes | Only one capture can run at a time. Stop older ones, wait 30 s, start again |
| A banking app shows a security warning | Some apps react to Developer Mode. Note it and skip that app |
| Phone still slow after a test | Run the "condition clear" command from step 7 |
| Numbers slower than the report | Check phone temperature and that charging and hotspot are off |
