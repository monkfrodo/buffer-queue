# buffer-queue

Keep your Buffer account full without opening Buffer. You write posts into a local `queue.json`, and a small script schedules them, channel by channel, up to Buffer's free-plan limit (10 scheduled posts per channel). Run it twice a day and the queue drains by itself.

No LLM, no server, no database. Just Python 3 and the official Buffer CLI.

[Leia em português](README.pt-BR.md)

## What it does

- Reads `queue.json`: each item has a due time and one text per channel.
- Schedules each item in Buffer until a channel reaches the limit.
- Never duplicates: if the same text is already in Buffer, it links to it instead.
- If an item's time has passed, it moves it to the next free slot of your posting grid.
- Saves the Buffer post id back into `queue.json`, so re-running is safe.
- `watchdog.py` warns you if the refill stopped running or the queue is almost empty.

## Fastest way: let an AI agent do it

Open [PROMPT.md](PROMPT.md), paste the prompt into Claude Code, Codex or a similar agent, and it walks you through the whole setup without ever seeing your API key.

## Setup (manual)

1. **Install the Buffer CLI** (needs Node.js):

   ```sh
   npm install --prefix ~/.local/share/buffer-cli @bufferapp/cli
   ```

   Point `buffer_cli` in `config.json` to `~/.local/share/buffer-cli/node_modules/.bin/buffer` (absolute path), or put `buffer` on your PATH.

2. **Create a Buffer API key** in your Buffer account settings. Treat it like a password.

3. **Store the key outside the project**, readable only by you:

   ```sh
   mkdir -p ~/.config/buffer-queue && chmod 700 ~/.config/buffer-queue
   read -rs KEY && printf %s "$KEY" > ~/.config/buffer-queue/api-key && unset KEY
   chmod 600 ~/.config/buffer-queue/api-key
   ```

   The key is never written to `config.json`, `queue.json` or the repo. Both are in `.gitignore`.

4. **Find your ids.** With the key loaded, list your organization and channels:

   ```sh
   export BUFFER_API_KEY="$(cat ~/.config/buffer-queue/api-key)"
   buffer account --output json
   buffer channels --help
   ```

   Organization and channel ids are identifiers, not secrets, but they are still yours. Keep them in `config.json` only.

5. **Create your config and queue:**

   ```sh
   cp config.example.json config.json
   cp examples/queue.example.json queue.json
   ```

   Edit `config.json`: your organization id, channel ids, timezone and posting grid. Channel names (`twitter`, `threads`, ...) must match Buffer's service names, because the script matches existing posts by service.

## The queue format

```json
[
 {
  "id": "any-unique-id",
  "due": "2026-01-02T09:30:00-03:00",
  "text": { "twitter": "Text for X", "threads": "Text for Threads" },
  "buffer": {}
 }
]
```

- `due`: ISO 8601 with offset. The script may move it if it is already past.
- `text`: one entry per channel. A channel missing here is skipped for that item.
- `buffer`: filled by the script with the Buffer post ids. Start with `{}`.

## Run it

```sh
export BUFFER_API_KEY="$(cat ~/.config/buffer-queue/api-key)"
python3 -I refill.py
```

Try it with one item first and look at Buffer before filling the whole queue.

## Run it automatically

**macOS (launchd).** Copy `launchd/com.example.buffer-refill.plist` to `~/Library/LaunchAgents/`, replace `/ABSOLUTE/PATH/TO/` with your real path, then:

```sh
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.buffer-refill.plist
launchctl kickstart gui/$(id -u)/com.example.buffer-refill
```

**Linux (cron):**

```cron
0 8,20 * * * BUFFER_API_KEY="$(cat $HOME/.config/buffer-queue/api-key)" /usr/bin/python3 -I /path/to/buffer-queue/refill.py >> /path/to/buffer-queue/refill.log 2>&1
```

Optional: run `python3 watchdog.py` a few times a day for a warning when the refill stalls.

## Keeping your account safe if you fork this

- Never commit `config.json`, `queue.json`, logs or any key. `.gitignore` covers them; check `git status` before every push.
- Never paste the key in chat, issues or pull requests. If it leaks, revoke it in Buffer and create a new one.
- Use a key dedicated to this tool, so you can revoke it without breaking anything else.

## License

MIT
