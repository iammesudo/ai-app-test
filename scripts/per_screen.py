"""Per-screen metrics for a walkthrough (tests/walk): CPU, memory, SmartNas data and servers per screen visit.
Usage: py -3.13 per_screen.py <walk_dir> [segments.json]
"""
import collections
import json
import re
import sys
from pathlib import Path

import pcapng

sys.path.insert(0, str(Path(__file__).parent))
from analyze import dns_answers, parse_ip, tls_sni  # noqa: E402

W = Path(sys.argv[1])
d = json.loads((W / "walk.json").read_text())
shots, perf = d["shots"], d["perf"]

# screenshot index ranges, labelled by looking at the contact sheets
SEG = [
    (0, 23, "Home"), (24, 25, "Top Up"), (26, 34, "SmartVIP points"), (35, 38, "History: balance"),
    (39, 49, "History: data usage"), (50, 53, "SmartVIP points"), (54, 59, "Points & discounts history"),
    (60, 65, "eVoucher Center"), (66, 89, "Top Up & payment options"), (90, 90, "eVoucher Center"),
    (91, 93, "SmartVIP restaurant deal"), (94, 100, "Outlet map & redeem"), (101, 114, "SmartVIP rewards"),
    (115, 118, "5G plans"), (119, 122, "5G coverage map"), (123, 125, "Device compatibility check"),
    (126, 131, "5G plans"), (132, 133, "Cybersecurity & Schedules"), (134, 138, "eSIM"),
    (139, 143, "Favorites"), (144, 163, "SmartRoam"), (164, 176, "Explore plans"),
    (177, 191, "Services & add-ons"), (192, 196, "Home Internet plans"), (197, 212, "Help & FAQ"),
    (213, 219, "Profile & Bong Smart chat"), (220, 227, "Switch account"), (228, 246, "Buying add-ons"),
    (247, 251, "Notifications"), (252, 255, "Home"), (256, 268, "Level Up & Daily Fortune game"),
    (269, 275, "Sign-in with OTP"), (276, 279, "Devices, payment methods, About"), (280, 287, "Help & FAQ"),
]
if len(sys.argv) > 2:  # [[first_shot, last_shot, "name"], ...]
    SEG = json.loads(Path(sys.argv[2]).read_text())
end_t = shots[-1]["t"] + 2
visits = []
for a, b, name in SEG:
    t0 = shots[a]["t"]
    t1 = shots[b + 1]["t"] if b + 1 < len(shots) else end_t
    visits.append({"name": name, "a": a, "b": b, "t0": t0, "t1": t1, "net": collections.Counter(), "up": 0, "down": 0})

for v in visits:
    ps = [p for p in perf if v["t0"] <= p["t"] < v["t1"]]
    v["sec"] = round(v["t1"] - v["t0"], 1)
    v["cpuAvg"] = round(sum(p["cpu"] for p in ps) / len(ps), 1) if ps else None
    v["cpuMax"] = max((p["cpu"] for p in ps), default=None)
    v["memMax"] = max((p["memMB"] for p in ps), default=None)
    v["memEnd"] = ps[-1]["memMB"] if ps else None
    w = [p["diskW"] for p in ps if p.get("diskW") is not None]
    v["diskMB"] = round((w[-1] - w[0]) / 1048576, 1) if len(w) > 1 else 0


def visit_at(t):
    for v in visits:
        if v["t0"] <= t < v["t1"]:
            return v


ip_names, sni_names = {}, {}
rx = re.compile(r"ProcName: ([^,]*), EPID: (-?\d+), EProcName: ([^,]*)")
with open(W / "network.pcapng", "rb") as f:
    try:
        for blk in pcapng.FileScanner(f):
            if not isinstance(blk, pcapng.blocks.EnhancedPacket):
                continue
            p = parse_ip(blk.packet_data)
            if not p:
                continue
            src, dst, proto, sp, dp, payload, ln = p
            if proto == "UDP" and sp == 53:
                for nm, a in dns_answers(payload):
                    ip_names.setdefault(a, nm)
            m = rx.search((blk.options.get("opt_comment", "") if blk.options else ""))
            if not m or "Runner" not in (m.group(1), m.group(3)):
                continue
            if src.is_private and dst.is_private:
                continue
            out = src.is_private or src.is_link_local
            remote = str(dst if out else src)
            if out and proto == "TCP":
                s = tls_sni(payload)
                if s:
                    sni_names[remote] = s
            v = visit_at(blk.timestamp)
            if v:
                v["up" if out else "down"] += ln
                v["net"][remote] += ln
    except Exception as e:
        print("pcap stopped:", e, file=sys.stderr)

for v in visits:
    hosts = collections.Counter()
    for ip, b in v["net"].items():
        hosts[sni_names.get(ip) or ip_names.get(ip) or ip] += b
    v["hosts"] = [(h, round(b / 1024, 1)) for h, b in hosts.most_common(6)]
    v["upKB"], v["downKB"] = round(v.pop("up") / 1024, 1), round(v.pop("down") / 1024, 1)
    del v["net"]
(W / "per_screen.json").write_text(json.dumps(visits, indent=1))
for v in visits:
    print(f"{v['name'][:30]:30} {v['sec']:6}s cpu {v['cpuAvg']}/{v['cpuMax']} mem {v['memMax']} disk {v['diskMB']}MB "
          f"up {v['upKB']}KB down {v['downKB']}KB {v['hosts'][:3]}")
