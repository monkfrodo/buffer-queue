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
3. Ask me to create a Buffer API key and store it at ~/.config/buffer-queue/api-key (README step 3). Wait until I confirm. Only verify the file exists with `test -s`.
4. With the key loaded only inside the command (export BUFFER_API_KEY="$(cat ~/.config/buffer-queue/api-key)" in the same shell call), run `buffer account --output json` and the channels command to find my organization id and channel ids. Show me only the ids and channel names, not any token.
5. Ask me which channels I want, my timezone, and the hours I want to post. Create config.json from config.example.json with those answers. Channel names must match Buffer's service names (twitter, threads, linkedin, ...).
6. Ask me for my posts, or help me write them, and build queue.json from examples/queue.example.json. One item per idea, one text per channel, a due time on my grid. Do not invent posts I did not approve.
7. Dry run with ONE item only: run `python3 -I refill.py`, then confirm in Buffer that exactly one post per channel was scheduled. Show me the log. If something fails, stop after two attempts at the same fix and tell me what you see.
8. Only after I approve the single post, run it for the whole queue.
9. Offer to schedule it twice a day (launchd on macOS, cron on Linux, see the README) and the watchdog. Do this only if I say yes.

Finish with a short summary: what is set up, where the files are, and the one command to run it again.
```
