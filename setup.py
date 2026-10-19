#!/usr/bin/env python3
"""Guided setup for buffer-queue. Run it once: python3 setup.py

It asks a few questions, saves your Buffer API key in a private file outside
this folder, finds your channels for you and writes config.json.
Your key is typed hidden and is never printed.
"""
import getpass
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_DIR = os.environ.get("BUFFER_QUEUE_KEY_DIR", os.path.expanduser("~/.config/buffer-queue"))
KEY_FILE = os.path.join(KEY_DIR, "api-key")
CLI_DIR = os.path.expanduser("~/.local/share/buffer-cli")
CLI = os.path.join(CLI_DIR, "node_modules", ".bin", "buffer")
DEFAULT_GRID = ["07:30", "09:30", "11:30", "13:30", "15:00", "17:00", "18:30", "21:00"]


def say(msg=""):
    print(msg, flush=True)


def ask(question, default=None):
    suffix = f" [{default}]" if default else ""
    answer = input(f"{question}{suffix}: ").strip()
    return answer or default


def step(n, title):
    say(f"\n--- Step {n}: {title} ---")


def buffer_json(*args):
    p = subprocess.run([CLI, *args, "--output", "json", "--quiet"], capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit("\nBuffer answered with an error. Most likely the API key is wrong or expired.\n"
                 "Create a new one in Buffer and run this setup again.")
    return json.loads(p.stdout)


def main():
    say("buffer-queue setup. It takes about 3 minutes.")

    step(1, "Buffer command-line tool")
    if not os.path.exists(CLI):
        if not shutil.which("npm"):
            sys.exit("This needs Node.js (it includes npm). Install it from https://nodejs.org and run this again.")
        say("Installing the official Buffer tool...")
        subprocess.run(["npm", "install", "--prefix", CLI_DIR, "@bufferapp/cli"], check=True)
    say("Buffer tool is ready.")

    step(2, "Your Buffer API key")
    if os.environ.get("BUFFER_API_KEY"):
        key = os.environ["BUFFER_API_KEY"]
        say("Using the key already in your environment.")
    elif os.path.exists(KEY_FILE) and (ask("A saved key already exists. Keep it? (y/n)", "y") or "y").lower().startswith("y"):
        key = open(KEY_FILE).read().strip()
    else:
        say("In Buffer, open your account settings, create an API key and copy it.")
        say("Paste it below. Nothing will appear on screen while you paste. That is normal.")
        key = getpass.getpass("API key: ").strip()
        if not key:
            sys.exit("No key received.")
    os.makedirs(KEY_DIR, mode=0o700, exist_ok=True)
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.write(fd, key.encode())
    os.close(fd)
    os.environ["BUFFER_API_KEY"] = key
    say(f"Key saved privately at {KEY_FILE} (only you can read it).")

    step(3, "Finding your Buffer account")
    account = buffer_json("account")
    orgs = account.get("organizations", [])
    if not orgs:
        sys.exit("No organization found in this Buffer account.")
    org = orgs[0]
    if len(orgs) > 1:
        for i, o in enumerate(orgs, 1):
            say(f"  {i}. organization {o['id']} ({o.get('channelCount', '?')} channels)")
        org = orgs[int(ask("Which one", "1")) - 1]
    channels = buffer_json("channels", "list", "--organization-id", org["id"])
    channels = channels if isinstance(channels, list) else channels.get("items", [])
    if not channels:
        sys.exit("No channels connected in Buffer yet. Connect one in Buffer and run this again.")

    step(4, "Choose where to post")
    for i, c in enumerate(channels, 1):
        say(f"  {i}. {c['service']:<10} {c.get('name', '')}")
    picked = ask("Numbers of the channels to use, separated by commas", ",".join(str(i) for i in range(1, len(channels) + 1)))
    chosen = {}
    for n in picked.split(","):
        c = channels[int(n) - 1]
        chosen[c["service"]] = c["id"]

    step(5, "Time zone and posting hours")
    tz = ask("Your time zone", account.get("timezone") or "UTC")
    say("Posts go out at these hours each day (edit config.json to change them later):")
    say("  " + ", ".join(DEFAULT_GRID))

    config = {"organization_id": org["id"], "channels": chosen, "limit": 10,
              "timezone": tz, "grid": DEFAULT_GRID, "buffer_cli": CLI}
    with open(os.path.join(HERE, "config.json"), "w") as f:
        json.dump(config, f, indent=2)
    queue = os.path.join(HERE, "queue.json")
    if not os.path.exists(queue):
        shutil.copy(os.path.join(HERE, "examples", "queue.example.json"), queue)

    say("\nDone. Nothing was posted yet.")
    say("Next: open queue.json, replace the example posts with yours, then run:  python3 refill.py")
    say("Channels in queue.json must be named: " + ", ".join(chosen))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit("\nCancelled.")
