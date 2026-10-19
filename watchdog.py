#!/usr/bin/env python3
"""Warn when the refill stopped or the queue is running low. Reads refill.log only; no secrets."""
import os, re, subprocess
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "refill.log")
MAX_AGE = timedelta(hours=14)
MIN_QUEUE = 20


def notify(msg):
    print(datetime.now().strftime("%F %T"), "ALERT", msg, flush=True)
    if os.path.exists("/usr/bin/osascript"):  # macOS notification; elsewhere the log line is enough
        script = 'display notification "%s" with title "Buffer refill stopped"' % msg
        subprocess.run(["/usr/bin/osascript", "-e", script])


lines = open(LOG, errors="replace").read().splitlines() if os.path.exists(LOG) else []
ok = [l for l in lines if re.match(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d left \d+ ", l)]
if not ok:
    notify("Refill has never finished successfully. Check refill.log")
else:
    last = ok[-1]
    when = datetime.strptime(last[:19], "%Y-%m-%d %H:%M:%S")  # log lines use the configured timezone
    left = int(re.search(r"left (\d+)", last).group(1))
    if datetime.now() - when > MAX_AGE:
        notify("Refill has not run since %s. Check refill.log" % last[:16])
    elif left < MIN_QUEUE:
        notify("Queue running low: %d posts left" % left)
