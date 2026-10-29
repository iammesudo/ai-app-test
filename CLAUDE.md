# iPhone app performance testing (instructions for Claude)

You help an engineer measure an iPhone app from a laptop over USB, using pymobiledevice3 (Apple developer services).
No jailbreak, the app is never modified. Read `README.md` for the layout and `FOR_AI.md` for the SmartNas data and how to read it.

## How to work
- Explain simply. The user may be new to this. Define a technical term the first time you use it.
- Run the commands yourself and report results. Do not hand the user a list of commands unless they ask for the do-it-yourself route.
- Follow `MAC_GUIDE.md` (Mac) or `REPRODUCE.md` (Windows). Run one step at a time and check its "Expected result" before the next.
- Lead with the answer, then the numbers. Say what you changed and what you left alone.
- If something fails, say so plainly, find the cause, fix it, and update the guide if the guide was wrong.

## Stop and ask the human before
Unlocking or touching the phone, tapping **Trust**, turning on Developer Mode, approving an admin or sudo prompt,
tapping through the app during a walkthrough, and anything that spends money (a purchase, a top-up, an eSIM). See `HUMAN_STEPS.md`.

## Hard rules (safety)
- Never type passwords, PINs, OTP codes or payment details. Never make a real purchase on your own.
- During a launch test the human must not touch the phone.
- After every slow-network test, always run the "condition clear" command, even if a step failed. Otherwise the phone stays slow.
- Network captures (`.pcapng`) contain ALL phone traffic. Screenshots can show ID cards, faces, QR codes, phone numbers, balances.
  Keep `out/` private: never commit it, upload it or paste it anywhere.
- Anything that goes to the repo or to other people must be scrubbed first: no screenshots, no raw captures,
  and logs with emails, phone numbers, names, long numbers, device IDs and container paths replaced by tags like `<email>`.
- `.gitignore` already blocks `out/`, `*.pcap*`, images. Do not weaken it.

## Keep the test fair
- Phone below 35 C: hotspot off, not fast-charging, out of its case. Check: `pymobiledevice3 diagnostics battery single` (Temperature / 100 = C).
- Same phone, same network, same day for every app you compare. Screen unlocked, auto-lock off, other apps closed.
- Run each launch test at least 3 times and report the median, not the best run.

## Units (always report in these)
- CPU: percent of ONE core (a 6-core phone maxes near 600). Not battery.
- Memory: iOS `physFootprint` in MB.
- Time to ready: seconds from the launch command until real data shows on screen (read from screenshots).
- Treat results as plus or minus 10 to 15 percent. Do not overclaim: one phone, one day; no battery data; network contents are encrypted.

## Setup facts
- Python 3.13 and `pymobiledevice3==11.34.0`. Python 3.14 fails to build a dependency (`pylzss`).
- The USB tunnel (`remote tunneld`) needs admin rights (Windows: admin terminal; Mac: `sudo`) and must stay open during tests.
- Scripts read the phone ID from the `UDID` environment variable.
- `--udid <UDID>` for syslog and pcap; `--tunnel <UDID>` for sysmon, screenshots, launch and conditions.

## Known problems
See the "Problems we hit" table in `REPRODUCE.md`. If you find a new one, add it there.

## If the Mac steps in `MAC_GUIDE.md` do not work
That guide was written from a Windows run and is not yet proven on a Mac. Fix the failing step, then edit `MAC_GUIDE.md`
so the next person does not hit it, and tell the user what you changed.
