"""Cold-start SmartNas several times, recording screenshots + CPU/memory, optionally on a fake slow network.
Usage: py -3.13 startup_test.py <out_dir> <runs> [network_profile_id] [bundle_id] [process_name]
Needs `pymobiledevice3 remote tunneld` running.
"""
import asyncio
import os
import io
import json
import sys
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageStat
from pymobiledevice3.services.dvt.instruments.condition_inducer import ConditionInducer
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.dvt.instruments.screenshot import Screenshot
from pymobiledevice3.services.dvt.instruments.sysmontap import Sysmontap
from pymobiledevice3.tunneld.api import get_tunneld_device_by_udid

UDID = os.environ.get("UDID", "<your-device-udid>")  # set with: export UDID=... (Mac) / $env:UDID=... (Windows)
BUNDLE = sys.argv[4] if len(sys.argv) > 4 else "smartnas"
PROC = sys.argv[5] if len(sys.argv) > 5 else "Runner"
WATCH_SEC = 25


def small(png: bytes) -> Image.Image:
    return Image.open(io.BytesIO(png)).convert("L").resize((118, 256))


def diff(a, b) -> float:
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


async def main(out: Path, runs: int, profile: str | None):
    out.mkdir(parents=True, exist_ok=True)
    rsd = await get_tunneld_device_by_udid(UDID)
    samples = []  # filled by the sysmon task: (time, cpu, memMB)

    async with DvtProvider(rsd) as dvt, ProcessControl(dvt) as pc, Screenshot(dvt) as shot, \
            await Sysmontap.create(dvt, interval=500) as sysmon:

        async def collect():
            async for procs in sysmon.iter_processes():
                for p in procs:
                    if p.get("name") == PROC:
                        samples.append((time.time(), round(p.get("cpuUsage") or 0, 1),
                                        round((p.get("physFootprint") or 0) / 1048576, 1)))
        collector = asyncio.create_task(collect())

        ci = None
        if profile:
            ci = ConditionInducer(dvt)
            await ci.__aenter__()
            await ci.set(profile)
        try:
            results = []
            for r in range(1, runs + 1):
                pid = await pc.process_identifier_for_bundle_identifier(BUNDLE)
                if pid:
                    await pc.kill(pid)
                await asyncio.sleep(4)  # let the phone settle on the home screen
                t0 = time.time()
                pid = await pc.launch(BUNDLE)
                shots, prev = [], None
                while time.time() - t0 < WATCH_SEC:
                    png = await shot.get_screenshot()
                    t = round(time.time() - t0, 2)
                    img = small(png)
                    name = f"run{r}_{t:05.1f}s.jpg"
                    Image.open(io.BytesIO(png)).convert("RGB").resize((393, 852)).save(out / name, quality=70)
                    change = round(diff(prev, img), 2) if prev else None
                    shots.append({"t": t, "file": name, "change": change})
                    prev = img
                perf = [{"t": round(s[0] - t0, 2), "cpu": s[1], "memMB": s[2]} for s in samples if t0 <= s[0] <= t0 + WATCH_SEC]
                results.append({"run": r, "pid": pid, "shots": shots, "perf": perf})
                print(f"run {r}: {len(shots)} screenshots, {len(perf)} perf samples", flush=True)
            (out / "results.json").write_text(json.dumps({"profile": profile, "runs": results}, indent=1))
        finally:
            if ci:
                await ci.service.disable_active_condition()
                await ci.__aexit__(None, None, None)
            collector.cancel()


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None))
