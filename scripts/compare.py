"""Summarize opening tests per app: effort/memory numbers + a contact sheet per test folder.
Usage: py -3.13 compare.py <tests_dir> <folder> [<folder> ...]
"""
import json
import statistics as st
import sys
from pathlib import Path

from PIL import Image, ImageDraw

T = Path(sys.argv[1])
for name in sys.argv[2:]:
    d = T / name
    f = d / "results.json"
    if not f.exists():
        print(name, "NO RESULTS")
        continue
    runs = json.loads(f.read_text())["runs"]
    for r in runs:
        p = r["perf"]
        late = [x["cpu"] for x in p if x["t"] > 15]
        first = next((s["t"] for s in r["shots"] if s["change"] and s["change"] > 20), None)
        print(f"{name} run{r['run']}: first-change {first}s | peak cpu {max((x['cpu'] for x in p), default=None)} "
              f"| cpu after 15s median {st.median(late) if late else None} | mem peak {max((x['memMB'] for x in p), default=None)} "
              f"end {p[-1]['memMB'] if p else None} | samples {len(p)}")
    r = runs[0]
    shots = r["shots"][::2]
    w, h, cols = 147, 320, 9
    rows = (len(shots) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * h), "white")
    for i, s in enumerate(shots):
        im = Image.open(d / s["file"]).resize((w, h))
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, 48, 16], fill="black")
        dr.text((3, 3), f"{s['t']}s", fill="yellow")
        sheet.paste(im, ((i % cols) * w, (i // cols) * h))
    sheet.save(T / f"sheet_{name.replace('/', '_')}.jpg", quality=70)
