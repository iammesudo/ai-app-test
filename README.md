# AI app testing kit (iPhone, from a laptop, with Claude)

Measure how an iPhone app really performs: launch time, CPU, memory, storage writes, network, and screen by screen.
No jailbreak. The app is not changed. You only need a USB cable. Claude runs the steps with you.

This kit was first used on **SmartNas 5.0.2** and compared with ABA, ACLEDA, Binance and Taobao (17 Oct 2026).

## Start here (new to this)

1. Install [Claude Code](https://claude.com/claude-code) and open it **inside this folder**.
   It reads `CLAUDE.md` by itself, so it already knows the tools, the rules and the safety limits.
2. Follow `MAC_GUIDE.md` once to set up your Mac and phone (about 30 minutes).
3. Say what you want in plain words. Examples are in `PROMPTS.md`.
4. When Claude asks you to do something with your hands, see `HUMAN_STEPS.md`.

## Which file for what

| I want to... | Open |
|---|---|
| Set up on a Mac | `MAC_GUIDE.md` |
| Set up on Windows | `REPRODUCE.md` |
| Know what to say to Claude | `PROMPTS.md` |
| Know what Claude cannot do for me | `HUMAN_STEPS.md` |
| Understand the SmartNas results | `DATA_README.md`, `FOR_AI.md` |
| Run the tests without Claude | `MAC_GUIDE.md` (every step has a command and an expected result) |
| Prove a finding in code | `REPRODUCE.md`, Part B (Xcode Instruments) |

## What is in this folder

- `scripts/`: the test tools (Python). `startup_test.py` launch test, `walk_rec.py` screen walkthrough,
  `pcap_rec.py` network capture, `analyze.py` / `per_screen.py` / `compare.py` summaries.
- `data/` and `logs/`: the cleaned SmartNas results. Drop `FOR_AI.md` and a CSV into any AI chat and it can explain them.
- No screenshots, no raw network captures, no personal data. Keep it that way (see `CLAUDE.md`).

## Limits to remember

One phone, one day. Treat numbers as plus or minus 10 to 15 percent. The ranking between apps is reliable; single seconds are not.
Battery is not measured. Network contents are encrypted, so you see where data goes and how much, not what it says.
