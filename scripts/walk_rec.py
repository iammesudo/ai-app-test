"""Record a manual walkthrough: a screenshot whenever the screen changes + SmartNas CPU/memory every 0.5 s.
Stops when a file named STOP appears in <out_dir>.
Usage: py -3.13 walk_rec.py <out_dir>
"""
import asyncio
import os
import io
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap
from pymobiledevice3.tunneld.api import get_tunneld_device_by_udid

UDID = os.environ.get("UDID", "<your-device-udid>")  # set with: export UDID=... (Mac) / $env:UDID=... (Windows)
CHANGE = 2.0  # mean pixel difference (0-255) on a small grey copy that counts as "screen changed"


async def main(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    stop = out / "STOP"
    rsd = await get_tunneld_device_by_udid(UDID)
    perf, shots = [], []
    async with DvtProvider(rsd) as dvt, Screenshot(dvt) as shot, await Sysmontap.create(dvt, interval=500) as sysmon:

        async def collect():
            async for procs in sysmon.iter_processes():
                for p in procs:
                    if p.get("name") == "Runner":
                        perf.append({"t": round(time.time(), 2), "cpu": round(p.get("cpuUsage") or 0, 1),
                                     "memMB": round((p.get("physFootprint") or 0) / 1048576, 1),
                                     "diskW": p.get("diskBytesWritten")})
        task = asyncio.create_task(collect())
        prev = None
        try:
            while not stop.exists():
                png = await shot.get_screenshot()
                t = time.time()
                img = Image.open(io.BytesIO(png))
                small = img.convert("L").resize((118, 256))
                change = ImageStat.Stat(ImageChops.difference(prev, small)).mean[0] if prev else 99
                if change >= CHANGE:
                    name = f"{time.strftime('%H%M%S', time.localtime(t))}_{int(t * 10) % 10}.jpg"
                    img.convert("RGB").resize((393, 852)).save(out / name, quality=70)
                    shots.append({"t": round(t, 2), "file": name, "change": round(change, 1)})
                    prev = small
                if len(shots) % 20 == 0:
                    (out / "walk.json").write_text(json.dumps({"shots": shots, "perf": perf}))
        finally:
            task.cancel()
            (out / "walk.json").write_text(json.dumps({"shots": shots, "perf": perf}))


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1])))
