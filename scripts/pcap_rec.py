"""Record iPhone network packets to a pcapng file, saving each packet as it arrives.
Stops cleanly when a file named STOP appears next to the output file.
Usage: py -3.13 pcap_rec.py <udid> <out.pcapng>
"""
import asyncio
import sys
from pathlib import Path

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.pcapd import PcapdService


async def main(udid: str, out_path: Path) -> None:
    stop = out_path.parent / "STOP"
    lockdown = await create_using_usbmux(serial=udid)
    service = PcapdService(lockdown=lockdown)

    class Flushing:  # pcapng writer only needs .write(); flush each block so a crash loses nothing
        def __init__(self, f):
            self.f = f

        def write(self, data):
            n = self.f.write(data)
            self.f.flush()
            return n

    async def until_stop():
        async for packet in service.watch(packets_count=-1):
            yield packet
            if stop.exists():
                return

    with out_path.open("wb") as f:
        await service.write_to_pcap(Flushing(f), until_stop())


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], Path(sys.argv[2])))
