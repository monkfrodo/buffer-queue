#!/usr/bin/env python3
"""Keep a Buffer account topped up from a local queue file. No LLM involved.

Every item in queue.json is already approved by you. For each channel the
script schedules posts up to Buffer's per-channel limit, skips text that is
already in Buffer (so it never duplicates), and moves overdue items to the
next free slot of your posting grid.

Usage: BUFFER_API_KEY=... python3 -I refill.py
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.environ.get("BUFFER_QUEUE_CONFIG", os.path.join(HERE, "config.json"))
QUEUE = os.environ.get("BUFFER_QUEUE_FILE", os.path.join(HERE, "queue.json"))
MARGIN = timedelta(minutes=20)


def load_config():
    if not os.path.exists(CONFIG):
        sys.exit(f"config not found: {CONFIG} (copy config.example.json to config.json)")
    cfg = json.load(open(CONFIG))
    cfg.setdefault("limit", 10)
    cfg.setdefault("timezone", "UTC")
    cfg.setdefault("buffer_cli", "buffer")
    return cfg


cfg = load_config()
TZ = ZoneInfo(cfg["timezone"])
ORG = cfg["organization_id"]
CHANNELS = cfg["channels"]  # {"name": "<buffer channel id>"}
LIMIT = cfg["limit"]
GRID = cfg["grid"]  # ["09:00", "13:00", ...] in the configured timezone


def log(*a):
    print(datetime.now(TZ).strftime("%F %T"), *a, flush=True)


def buffer(*args):
    p = subprocess.run([cfg["buffer_cli"], *args, "--output", "json", "--quiet"],
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def list_posts(filt):
    items, cur = [], None
    while True:
        args = ["posts", "list", "--json", json.dumps({"organizationId": ORG, "filter": filt}),
                "--limit", "100", "--fields", "items.{id,status,dueAt,text,channel.service},pageInfo"]
        if cur:
            args += ["--after", cur]
        rc, out, err = buffer(*args)
        if rc != 0:
            raise RuntimeError(f"posts list failed: {err.strip()[:300]}")
        d = json.loads(out)
        items += d["items"]
        if not d["pageInfo"]["hasNextPage"]:
            return items
        cur = d["pageInfo"]["endCursor"]


def norm(t):
    return " ".join((t or "").split())


def parse(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def next_slot(after, taken):
    day = after.astimezone(TZ).date()
    while True:
        for hm in GRID:
            h, m = map(int, hm.split(":"))
            t = datetime(day.year, day.month, day.day, h, m, tzinfo=TZ)
            if t > after and t.isoformat() not in taken:
                return t
        day += timedelta(days=1)


def save(queue):
    with open(QUEUE + ".tmp", "w") as f:
        json.dump(queue, f, ensure_ascii=False, indent=1)
    os.replace(QUEUE + ".tmp", QUEUE)


def main():
    queue = json.load(open(QUEUE))
    now = datetime.now(TZ)
    recent = list_posts({"dueAt": {"start": (now - timedelta(days=21)).isoformat()}})
    seen = {(p["channel"]["service"], norm(p["text"])): p["id"] for p in recent}
    count = {ch: 0 for ch in CHANNELS}
    for p in recent:
        if p["status"] == "scheduled" and p["channel"]["service"] in count:
            count[p["channel"]["service"]] += 1
    log("scheduled in Buffer:", count)

    changed = False
    for item in sorted(queue, key=lambda i: i["due"]):
        item.setdefault("buffer", {})
        todo = [ch for ch in CHANNELS if ch in item["text"] and not item["buffer"].get(ch)]
        if not todo:
            continue
        for ch in todo:
            hit = seen.get((ch, norm(item["text"][ch])))
            if hit:
                item["buffer"][ch] = hit
                changed = True
                log(item["id"], ch, "already in Buffer", hit)
        todo = [ch for ch in todo if not item["buffer"].get(ch) and count[ch] < LIMIT]
        if not todo:
            continue
        if parse(item["due"]) < now + MARGIN:
            taken = {i["due"] for i in queue if i is not item}
            last = max([parse(i["due"]) for i in queue if any(i["buffer"].values())] + [now + MARGIN])
            item["due"] = next_slot(last, taken).isoformat()
            changed = True
            log(item["id"], "rescheduled to", item["due"])
        for ch in todo:
            payload = {"channelId": CHANNELS[ch], "schedulingType": "automatic",
                       "mode": "customScheduled", "dueAt": item["due"], "text": item["text"][ch]}
            rc, out, err = buffer("posts", "create", "--json", json.dumps(payload, ensure_ascii=False))
            if rc == 0:
                pid = (json.loads(out).get("post") or {}).get("id")
                if pid:
                    item["buffer"][ch] = pid
                    count[ch] += 1
                    changed = True
                    log(item["id"], ch, "scheduled", item["due"], pid)
                else:
                    log(item["id"], ch, "response without id:", out.strip()[:300])
            else:
                log(item["id"], ch, "ERROR:", err.strip()[:300])
                if "limit" in err.lower():
                    count[ch] = LIMIT
        if changed:
            save(queue)
            changed = False
    if changed:
        save(queue)

    left = sum(1 for i in queue for ch in CHANNELS if ch in i["text"] and not i["buffer"].get(ch))
    log("left", left, "posts unscheduled")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("FAILED:", e)
        sys.exit(1)
