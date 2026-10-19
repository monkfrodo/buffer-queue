# Set this up with an AI coding agent

Paste the prompt below into Claude Code, Codex or any agent that can run shell commands on your machine. It sets up buffer-queue for you and keeps your API key out of the chat.

---

```text
Set up the open-source project https://github.com/monkfrodo/buffer-queue on this machine so it keeps my Buffer account filled from a local queue file. Read its README.md first and follow it.

Rules you must follow:
- NEVER ask me to paste my Buffer API key in this chat, and never print it, log it, echo it, or write it into any file inside the project. If you need it, tell me to run the command that stores it myself (the `read -rs KEY ...` command from the README step 3, with `! ` in front if I'm in Claude Code) and then only check that the file exists.
- Never run `env`, `printenv` or `cat` on the key file.
- Never commit config.json, queue.json, logs or keys. Check `git status` before any commit.

Do this, in order:
1. Clone the repo into ~/Developer/buffer-queue and check that python3 and node are installed (tell me what to install if not).
2. Install the Buffer CLI: npm install --prefix ~/.local/share/buffer-cli @bufferapp/cli
3. Tell me to run `python3 setup.py` MYSELF in this folder (in Claude Code I can type `! python3 setup.py`) because it asks for my Buffer API key with hidden input. Do not run it for me and do not ask me to paste the key here. Wait until I say it finished. Then just check that config.json exists.
4. Read config.json (it has no secrets) and tell me which channels are configured and the posting hours. Ask if I want to change the hours or timezone and edit config.json if so.
5. Ask me where my content comes from. If I have a Substack or blog, run `python3 import_feed.py <address>` (public feed, no key needed) so my articles become drafts. Otherwise help me write posts in queue.json from examples/queue.example.json. Never invent posts I did not write. Then tell me to run `python3 serve.py`, open http://127.0.0.1:8765, and approve the posts I want. Imported items stay drafts until I approve them; never set `status` to approved for me.
6. Dry run with ONE approved item only: run `python3 -I refill.py`, then confirm in Buffer that exactly one post per channel was scheduled. Show me the log. If something fails, stop after two attempts at the same fix and tell me what you see.
7. Only after I approve the single post, run it for the whole queue.
8. Offer to schedule it twice a day (launchd on macOS, cron on Linux, see the README) and the watchdog. Do this only if I say yes.

Finish with a short summary: what is set up, where the files are, and the one command to run it again.
```
