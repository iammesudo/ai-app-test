# What Claude cannot do for you

Claude runs the commands, but these need a person. Claude will stop and ask you at each one.

| When | What you do | Why |
|---|---|---|
| First connection | Unlock the phone and tap **Trust** | Apple asks the phone's owner, no software can answer for you |
| First time on a phone | Turn on **Developer Mode** (Settings, Privacy & Security, Developer Mode, On, Restart) | Needs a restart and your passcode |
| Starting the USB tunnel | Type your Mac password (`sudo`) | Admin permission is yours to give |
| Launch tests | **Do not touch the phone** for the 25 s of each run | Touches change the result |
| Walkthrough | Tap through the app yourself | Claude cannot reach the phone's screen to tap |
| Anything that costs money | Do the payment yourself | Claude never makes purchases and never types payment details |
| Login, OTP, PIN, face check | Do these yourself | Claude never types passwords, codes or PINs |
| Phone too hot (35 C or more) | Unplug the charger, turn off hotspot, wait until it cools | A hot phone slows every app and makes results unfair |

## Before you start every test day
- [ ] Phone below 35 C, hotspot off, not fast-charging, out of its case
- [ ] Screen unlocked, auto-lock off, other apps closed
- [ ] Same phone and same network for every app you compare
- [ ] The USB tunnel window is open

## After every test
- [ ] Slow network cleared (`condition clear`)
- [ ] Recordings kept in `out/` only. Never share `out/`: it has screenshots and full network captures
- [ ] Before sharing anything: no screenshots, no raw captures, no personal details
