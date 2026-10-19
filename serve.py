#!/usr/bin/env python3
"""A small page on your own computer to review, edit and approve your queue.

Usage: python3 serve.py      then open http://127.0.0.1:8765
It only listens on your computer (127.0.0.1). Nothing leaves your machine
until you run refill.py, and refill.py only schedules approved posts.
"""
import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import refill

PORT = int(os.environ.get("BUFFER_QUEUE_PORT", "8765"))
UI = os.path.join(refill.HERE, "ui", "index.html")


def load():
    return json.load(open(refill.QUEUE)) if os.path.exists(refill.QUEUE) else []


def to_view(i):
    due = refill.parse(i["due"]).astimezone(refill.TZ)
    return {"id": i["id"], "due_local": due.strftime("%Y-%m-%dT%H:%M"),
            "status": i.get("status", "approved"), "source": i.get("source", ""),
            "scheduled": any(i.get("buffer", {}).values()), "text": i.get("text", {})}


def state():
    items = sorted(load(), key=lambda i: i["due"])
    return {"timezone": str(refill.TZ), "channels": list(refill.CHANNELS),
            "items": [to_view(i) for i in items]}


def save(view_items):
    old = {i["id"]: i for i in load()}
    out, seen = [], set()
    for v in view_items:
        iid = str(v["id"]).strip()
        if not iid or iid in seen:
            raise ValueError(f"empty or repeated id: {iid!r}")
        seen.add(iid)
        prev = old.get(iid)
        if prev and any(prev.get("buffer", {}).values()):
            out.append(prev)  # already in Buffer: edits here would not change it
            continue
        due = datetime.strptime(v["due_local"], "%Y-%m-%dT%H:%M").replace(tzinfo=refill.TZ)
        text = {ch: t for ch, t in v.get("text", {}).items() if ch in refill.CHANNELS and t.strip()}
        item = {"id": iid, "due": due.isoformat(),
                "status": "approved" if v.get("status") == "approved" else "draft",
                "text": text, "buffer": (prev or {}).get("buffer", {})}
        if v.get("source"):
            item["source"] = v["source"]
        out.append(item)
    for iid, prev in old.items():  # never lose something already scheduled
        if iid not in seen and any(prev.get("buffer", {}).values()):
            out.append(prev)
    refill.save(out)


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def ok_host(self):
        return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")

    def send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self.ok_host():
            return self.send(403, "{}")
        if self.path == "/api/state":
            return self.send(200, json.dumps(state()))
        if self.path in ("/", "/index.html"):
            return self.send(200, open(UI, "rb").read(), "text/html")
        self.send(404, "{}")

    def do_POST(self):
        # Custom header: a web page on another site cannot send it, so it cannot change your queue.
        if not self.ok_host() or self.headers.get("X-Buffer-Queue") != "1" or self.path != "/api/save":
            return self.send(403, "{}")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            save(body["items"])
            self.send(200, json.dumps(state()))
        except Exception as ex:
            self.send(400, json.dumps({"error": str(ex)}))


if __name__ == "__main__":
    try:
        srv = HTTPServer(("127.0.0.1", PORT), H)
    except OSError:
        sys.exit(f"Port {PORT} is busy. Close the other copy, or set BUFFER_QUEUE_PORT=8766")
    print(f"Queue page: http://127.0.0.1:{PORT}   (Ctrl+C to stop)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
