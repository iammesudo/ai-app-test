"""Summarize a SmartNas capture folder into summary.json.
Usage: py -3.13 analyze.py <capture_dir> [process_name]
"""
import collections
import ipaddress
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import pcapng

DIR = Path(sys.argv[1])
PROC = sys.argv[2] if len(sys.argv) > 2 else "Runner"
MB = 1024 * 1024


def iso(ts):
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


# ---------- CPU / memory ----------
def perf():
    rows = [json.loads(l) for l in open(DIR / "perf.jsonl", encoding="utf-8") if l.strip()]
    tl = []
    for r in rows:
        t = datetime.fromisoformat(r["timestamp"]).astimezone().timestamp()
        tl.append({
            "t": round(t, 1),
            "cpu": round(r.get("cpuUsage") or 0, 1),
            "memMB": round((r.get("physFootprint") or 0) / MB, 1),
            "threads": r.get("threadCount"),
            "diskWriteMB": round((r.get("diskBytesWritten") or 0) / MB, 2),
            "diskReadMB": round((r.get("diskBytesRead") or 0) / MB, 2),
            "wakeups": r.get("intWakeups"),
            "power": round(r.get("powerScore") or 0, 1),
            "pid": r.get("pid"),
        })
    cpus = [x["cpu"] for x in tl]
    mems = [x["memMB"] for x in tl]
    peak_cpu = max(tl, key=lambda x: x["cpu"])
    peak_mem = max(tl, key=lambda x: x["memMB"])
    return {
        "samples": len(tl),
        "start": iso(tl[0]["t"]), "end": iso(tl[-1]["t"]),
        "durationSec": round(tl[-1]["t"] - tl[0]["t"]),
        "pids": sorted({x["pid"] for x in tl}),
        "cpuAvg": round(sum(cpus) / len(cpus), 1),
        "cpuPeak": peak_cpu["cpu"], "cpuPeakAt": iso(peak_cpu["t"]),
        "secondsOver50pct": sum(1 for c in cpus if c > 50),
        "secondsOver100pct": sum(1 for c in cpus if c > 100),
        "memStartMB": mems[0], "memEndMB": mems[-1],
        "memPeakMB": peak_mem["memMB"], "memPeakAt": iso(peak_mem["t"]),
        "threadsMax": max(x["threads"] or 0 for x in tl),
        "diskWrittenMB": round(tl[-1]["diskWriteMB"] - tl[0]["diskWriteMB"], 2),
        "diskReadMB": round(tl[-1]["diskReadMB"] - tl[0]["diskReadMB"], 2),
        "timeline": tl,
    }


# ---------- network ----------
def parse_ip(data):
    """Return (src, dst, proto, sport, dport, payload, length) or None. Frame has a 14-byte fake ethernet header."""
    if len(data) < 14:
        return None
    etype = struct.unpack("!H", data[12:14])[0]
    ip = data[14:]
    if etype == 0x0800 and len(ip) >= 20:
        ihl = (ip[0] & 15) * 4
        proto = ip[9]
        src, dst = ipaddress.ip_address(ip[12:16]), ipaddress.ip_address(ip[16:20])
        l4 = ip[ihl:]
        total = struct.unpack("!H", ip[2:4])[0]
    elif etype == 0x86DD and len(ip) >= 40:
        proto = ip[6]
        src, dst = ipaddress.ip_address(ip[8:24]), ipaddress.ip_address(ip[24:40])
        l4 = ip[40:]
        total = 40 + struct.unpack("!H", ip[4:6])[0]
    else:
        return None
    if proto == 6 and len(l4) >= 20:
        sp, dp = struct.unpack("!HH", l4[:4])
        off = (l4[12] >> 4) * 4
        return src, dst, "TCP", sp, dp, l4[off:], total
    if proto == 17 and len(l4) >= 8:
        sp, dp = struct.unpack("!HH", l4[:4])
        return src, dst, "UDP", sp, dp, l4[8:], total
    return src, dst, str(proto), 0, 0, b"", total


def dns_answers(payload):
    """Very small DNS response parser: yields (name, ip)."""
    try:
        qd, an = struct.unpack("!HH", payload[4:8])
        if not payload[2] & 0x80:
            return []

        def name(off, depth=0):
            labels = []
            while depth < 20:
                n = payload[off]
                if n == 0:
                    return ".".join(labels), off + 1
                if n & 0xC0 == 0xC0:
                    ptr = struct.unpack("!H", payload[off:off + 2])[0] & 0x3FFF
                    return ".".join(labels + [name(ptr, depth + 1)[0]]), off + 2
                labels.append(payload[off + 1:off + 1 + n].decode(errors="replace"))
                off += 1 + n
            raise ValueError
        off = 12
        for _ in range(qd):
            _, off = name(off)
            off += 4
        out = []
        for _ in range(an):
            nm, off = name(off)
            typ, _, _, rdlen = struct.unpack("!HHIH", payload[off:off + 10])
            off += 10
            rd = payload[off:off + rdlen]
            off += rdlen
            if typ == 1 and rdlen == 4:
                out.append((nm, str(ipaddress.ip_address(rd))))
            elif typ == 28 and rdlen == 16:
                out.append((nm, str(ipaddress.ip_address(rd))))
        return out
    except Exception:
        return []


def tls_sni(payload):
    """Hostname from a TLS ClientHello, or None."""
    try:
        if payload[0] != 0x16 or payload[5] != 0x01:
            return None
        p = 43
        p += 1 + payload[p]
        p += 2 + struct.unpack("!H", payload[p:p + 2])[0]
        p += 1 + payload[p]
        end = p + 2 + struct.unpack("!H", payload[p:p + 2])[0]
        p += 2
        while p + 4 <= end:
            et, el = struct.unpack("!HH", payload[p:p + 4])
            if et == 0:
                ln = struct.unpack("!H", payload[p + 7:p + 9])[0]
                return payload[p + 9:p + 9 + ln].decode()
            p += 4 + el
    except Exception:
        return None


def network():
    comment_re = re.compile(r"ProcName: ([^,]*), EPID: (-?\d+), EProcName: ([^,]*)")
    ip_names = {}
    hosts = collections.defaultdict(lambda: {"up": 0, "down": 0, "packets": 0, "first": None, "last": None,
                                             "ports": set(), "proto": set(), "sni": set()})
    per_proc = collections.Counter()
    per_sec = collections.Counter()
    total_pk = app_pk = 0
    conns = set()
    with open(DIR / "network.pcapng", "rb") as f:
        scanner = pcapng.FileScanner(f)
        try:
            for blk in scanner:
                if not isinstance(blk, pcapng.blocks.EnhancedPacket):
                    continue
                total_pk += 1
                c = blk.options.get("opt_comment", "") if blk.options else ""
                m = comment_re.search(c)
                proc, eproc = (m.group(1), m.group(3)) if m else ("?", "?")
                parsed = parse_ip(blk.packet_data)
                if not parsed:
                    continue
                src, dst, proto, sp, dp, payload, ln = parsed
                if proto == "UDP" and sp == 53:
                    for nm, a in dns_answers(payload):
                        ip_names.setdefault(a, nm)
                per_proc[proc or eproc or "?"] += ln
                if PROC not in (proc, eproc):
                    continue
                app_pk += 1
                ts = blk.timestamp
                outgoing = src.is_private or src.is_link_local
                remote, rport = (dst, dp) if outgoing else (src, sp)
                if remote.is_private and (dst.is_private and src.is_private):
                    continue  # USB tunnel / local traffic
                h = hosts[str(remote)]
                h["up" if outgoing else "down"] += ln
                h["packets"] += 1
                h["first"] = h["first"] or ts
                h["last"] = ts
                h["ports"].add(rport)
                h["proto"].add(proto)
                if outgoing and proto == "TCP":
                    conns.add((str(remote), sp))
                    s = tls_sni(payload)
                    if s:
                        h["sni"].add(s)
                per_sec[int(ts)] += ln
        except Exception as e:  # truncated last block from a killed capture is fine
            print("pcap read stopped:", e, file=sys.stderr)

    out = []
    for ip, h in hosts.items():
        name = sorted(h["sni"])[0] if h["sni"] else ip_names.get(ip, "")
        out.append({"ip": ip, "host": name, "sni": sorted(h["sni"]), "upKB": round(h["up"] / 1024, 1),
                    "downKB": round(h["down"] / 1024, 1), "packets": h["packets"],
                    "first": iso(h["first"]), "last": iso(h["last"]),
                    "ports": sorted(h["ports"]), "proto": sorted(h["proto"])})
    out.sort(key=lambda x: -(x["upKB"] + x["downKB"]))
    # group by hostname (several IPs may serve one host)
    by_host = collections.defaultdict(lambda: {"upKB": 0, "downKB": 0, "ips": [], "first": "99", "last": "00"})
    for o in out:
        k = o["host"] or o["ip"]
        g = by_host[k]
        g["upKB"] = round(g["upKB"] + o["upKB"], 1)
        g["downKB"] = round(g["downKB"] + o["downKB"], 1)
        g["ips"].append(o["ip"])
        g["first"] = min(g["first"], o["first"])
        g["last"] = max(g["last"], o["last"])
        g["ports"] = sorted(set(g.get("ports", [])) | set(o["ports"]))
    hosts_list = sorted(({"host": k, **v} for k, v in by_host.items()), key=lambda x: -(x["upKB"] + x["downKB"]))
    return {
        "totalPackets": total_pk, "appPackets": app_pk,
        "appUpKB": round(sum(o["upKB"] for o in out), 1),
        "appDownKB": round(sum(o["downKB"] for o in out), 1),
        "tcpConnections": len(conns),
        "topProcessesKB": [(p, round(b / 1024)) for p, b in per_proc.most_common(12)],
        "hosts": hosts_list,
        "perSecondKB": sorted((iso(t), round(b / 1024, 1)) for t, b in per_sec.items()),
    }


# ---------- logs ----------
SECRET = re.compile(r"(?i)(bearer\s+[\w\-.]+|token[\"'=: ]+[\w\-.]{12,}|eyJ[\w\-]+\.[\w\-]+\.[\w\-]+|password[\"'=: ]+\S+)")


def logs():
    levels = collections.Counter()
    subsys = collections.Counter()
    errors = collections.Counter()
    urls = collections.Counter()
    app_msgs = collections.Counter()
    secrets = 0
    per_min = collections.Counter()
    n = 0
    url_re = re.compile(r"https?://[^\s\"'<>)]+")
    with open(DIR / "app-log.jsonl", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            n += 1
            msg = e.get("message") or ""
            lab = e.get("label") or {}
            ss = lab.get("subsystem") or "(none)"
            levels[e.get("level")] += 1
            subsys[ss] += 1
            per_min[e["timestamp"][11:16]] += 1
            if SECRET.search(msg):
                secrets += 1
            for u in url_re.findall(msg):
                urls[re.sub(r"\?.*", "?…", u)[:120]] += 1
            short = re.sub(r"0x[0-9a-f]+|\d+", "#", msg)[:140]
            if e.get("level") in ("ERROR", "FAULT") or re.search(r"(?i)\b(error|fail|denied|timeout|crash)", msg):
                errors[f"[{ss}] {short}"] += 1
            img = e.get("image_name") or ""
            if "Runner.app" in img or ss == "(none)" or "flutter" in ss.lower():
                app_msgs[SECRET.sub("[REDACTED]", short)] += 1
    return {
        "entries": n, "levels": dict(levels), "perMinute": sorted(per_min.items()),
        "topSubsystems": subsys.most_common(15),
        "topErrors": errors.most_common(25),
        "urls": urls.most_common(30),
        "appOwnMessages": app_msgs.most_common(25),
        "linesThatLookLikeSecrets": secrets,
    }


if __name__ == "__main__":
    summary = {"perf": perf(), "network": network(), "logs": logs()}
    (DIR / "summary.json").write_text(json.dumps(summary, indent=1, default=list), encoding="utf-8")
    p, nw, lg = summary["perf"], summary["network"], summary["logs"]
    tl = p.pop("timeline")
    print(json.dumps(p, indent=1))
    print(json.dumps({k: v for k, v in nw.items() if k != "perSecondKB"}, indent=1, default=list)[:6000])
    print(json.dumps(lg, indent=1)[:8000])
