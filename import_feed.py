#!/usr/bin/env python3
"""Turn the articles of a blog feed into draft posts in queue.json.

Works with any RSS or Atom feed, and with Substack: just give the address.
Nothing is scheduled. New items arrive as drafts; you review, edit and approve
them in the queue page (python3 serve.py).

Usage:
  python3 import_feed.py yourname.substack.com
  python3 import_feed.py https://example.com/feed.xml --limit 10
"""
import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import refill  # loads config.json; gives us the grid, timezone and channels

# Rough character limits per network. Unknown networks get a generous default.
LIMITS = {"twitter": 280, "bluesky": 300, "threads": 500, "mastodon": 500,
          "linkedin": 3000, "facebook": 3000, "instagram": 2200}
LINK_COST = 24  # X counts every link as 23 characters, plus a space


def feed_url(arg):
    if "://" not in arg:
        arg = "https://" + arg
    if "substack.com" in arg and "/feed" not in arg:
        arg = arg.rstrip("/") + "/feed"
    return arg


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "buffer-queue"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def entries(xml):
    root = ET.fromstring(xml)
    out = []
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        g = lambda n: next((c for c in it if c.tag.split("}")[-1] == n), None)
        title = (g("title").text or "").strip() if g("title") is not None else ""
        link = ""
        l = g("link")
        if l is not None:
            link = (l.text or l.attrib.get("href") or "").strip()
        desc = g("description") if g("description") is not None else g("summary")
        text = re.sub(r"<[^>]+>", " ", (desc.text or "") if desc is not None else "")
        text = " ".join(text.split())
        if title and link:
            out.append({"title": title, "link": link, "summary": text})
    return out


def make_text(ch, e):
    limit = LIMITS.get(ch, 3000)
    head = e["title"]
    room = limit - LINK_COST - 2
    if len(head) > room:
        head = head[: room - 1].rstrip() + "…"
    return f'{head}\n\n{e["link"]}'


def slug(link):
    return re.sub(r"[^a-z0-9]+", "-", link.split("://")[-1].lower()).strip("-")[-60:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("feed", help="Substack address, blog address or feed URL")
    ap.add_argument("--limit", type=int, default=10, help="how many newest articles to import (default 10)")
    args = ap.parse_args()

    queue = json.load(open(refill.QUEUE)) if refill.os.path.exists(refill.QUEUE) else []
    known = {i.get("source") for i in queue}
    try:
        found = entries(fetch(feed_url(args.feed)))
    except Exception as ex:
        sys.exit(f"Could not read that feed: {ex}")
    if not found:
        sys.exit("No articles found. Check the address.")

    now = datetime.now(refill.TZ)
    taken = {i["due"] for i in queue}
    last = max([refill.parse(i["due"]) for i in queue] + [now])
    added = 0
    for e in found[: args.limit]:
        if e["link"] in known:
            continue
        slot = refill.next_slot(last, taken)
        last = slot
        taken.add(slot.isoformat())
        queue.append({
            "id": f'{slot:%Y-%m-%d}_{slug(e["link"])}',
            "due": slot.isoformat(),
            "status": "draft",
            "source": e["link"],
            "text": {ch: make_text(ch, e) for ch in refill.CHANNELS},
            "buffer": {},
        })
        added += 1
        print("draft:", e["title"])
    refill.save(queue)
    print(f"\n{added} new draft(s) added. Review them: python3 serve.py")


if __name__ == "__main__":
    main()
