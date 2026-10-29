# What to say to Claude

Plain words work. These are real examples of what was asked in the first project, grouped by job.
Replace `SmartNas` with your app.

## Get started
- "Set up this Mac for testing and check that the phone is connected."
- "Check the phone temperature. Is it cool enough for a fair test?"
- "List the apps on the phone and find the bundle ID and process name for SmartNas."

## Launch speed
- "Run the launch test on SmartNas 3 times and show me the median ready time."
- "Now run it on a very poor simulated network, then clear it."
- "Compare SmartNas with ABA on launch. Which is faster and by how much?"
- "The developer says Firebase shows 2.5 s but we saw 5 s. Explain why the numbers can differ, and measure it the same way as Firebase."

## Screens and walkthrough
- "I will tap through the app. Record screenshots, CPU and memory, and stop when I say done."
- "Name the screens from the frames and make a per-screen report."
- "Which screen uses the most CPU or memory?"
- "Which screens are slow, and what was the app waiting on?"

## Network
- "Where does the data go? Group the servers by owner and show the biggest."
- "How much data does the Home screen use in a minute?"

## Compare builds or apps
- "Compare this build with the last results in `data/`. What got faster or slower?"
- "Compare idle CPU for all five apps."

## Understand existing results
- "Read `FOR_AI.md` and the CSVs. Summarise the three biggest problems in plain words."
- "Is the idle CPU of 44% real? Show me from the raw samples."
- "Which finding would you check first with Xcode Instruments, and how?"

## Reports
- "Make a one-page summary for a product manager: plain words, numbers first."
- "Make a developer note: what we measured, how, and what to check in the code."

## Safety phrases Claude should keep to
- Claude will ask you to unlock, tap Trust, approve the password, or tap through the app. That is normal.
- If it tries to type a password or make a payment, stop it. It should never do that.
- Before sharing any result outside the team, say: "Scrub this for sharing, no screenshots or personal data."

## When things go wrong
- "That failed. Find the cause, fix it, and update `MAC_GUIDE.md` so the next person does not hit it."
- "The numbers look much slower than the report. Check the temperature and whether charging or hotspot is on."
