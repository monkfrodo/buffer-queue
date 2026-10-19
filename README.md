# buffer-queue

**Write your social media posts once. Let them go out by themselves for weeks.**

![How it works: your posts, this tool, Buffer, your social networks](docs/img/how-it-works.svg)

[Leia em português](README.pt-BR.md)

## What is this?

[Buffer](https://buffer.com) is a free tool that publishes posts on your social networks at the time you choose. Its free plan lets you keep only **10 scheduled posts per network** at a time. So every few days you must go back and schedule more.

**buffer-queue removes that chore.** You keep all your future posts in one simple text file. Twice a day, this tool checks Buffer, sees which networks have room, and schedules the next posts for you. You write posts whenever you feel like it. The tool does the scheduling.

It is free, runs on your own computer, has no AI and no server, and your posts never go anywhere except Buffer.

## What you need

| You need | Where to get it |
|---|---|
| A free Buffer account with at least one social network connected | [buffer.com](https://buffer.com) |
| Python 3 | Already on Mac. On Windows: [python.org/downloads](https://www.python.org/downloads/) (tick "Add Python to PATH") |
| Node.js (to install Buffer's official tool) | [nodejs.org](https://nodejs.org) (the "LTS" button) |

If you prefer, an AI assistant can do the whole setup with you: see [PROMPT.md](PROMPT.md).

## Setup in 4 steps

![Setup: download, run the setup, write your posts, run it](docs/img/steps.svg)

### 1. Download this project

On this page, click the green **Code** button, then **Download ZIP**. Open the ZIP so it becomes a folder called `buffer-queue-main`.

### 2. Run the guided setup

Open a terminal inside that folder.

- **Mac:** press `Cmd + Space`, type `Terminal`, press Enter. Type `cd ` (with a space), drag the `buffer-queue-main` folder into the window, press Enter.
- **Windows:** open the folder, click the address bar, type `powershell`, press Enter.

Then run:

```sh
python3 setup.py
```

(On Windows, use `python setup.py`.)

It asks a few questions and does the rest. This is what you will see (the account name is made up):

![Terminal showing the guided setup](docs/img/terminal-setup.png)

What it does:

1. Installs Buffer's official tool, if missing.
2. Asks for your **Buffer API key**. This is like a password that lets this tool schedule posts for you. Create one in your Buffer account settings (look for the API or developer section; [Buffer's help center](https://support.buffer.com) has the current steps). Paste it when asked. **Nothing shows on screen while you paste. That is normal.**
3. Finds your Buffer account and lists your connected networks. You pick the ones to use.
4. Asks your time zone and saves everything.

Your key is saved in a private file on your computer, outside this folder. It is never inside the project, so you cannot publish it by accident.

### 3. Write your posts

Open `queue.json` in any text editor. The setup created it with two example posts. Replace them with yours. Each post looks like this:

![Anatomy of a post in queue.json](docs/img/queue-anatomy.svg)

Tips:

- Copy a whole post block, paste it right after, and edit. Keep the commas between blocks.
- The network names under `text` must be the ones the setup printed (for example `twitter`, `threads`, `linkedin`).
- You can leave a network out of a post to skip it for that one.
- If you break the file, a free checker like [jsonlint.com](https://jsonlint.com) shows where.

### 4. Run it

First, make sure the queue only has **one or two posts**, then:

```sh
python3 refill.py
```

The result looks like this:

![Terminal showing two posts scheduled on two networks](docs/img/terminal-refill.png)

Open Buffer. You should see those posts scheduled, like in this illustration:

![Illustration of the Buffer queue with two scheduled posts](docs/img/buffer-result.svg)

The terminal screens above are real output from this tool, run against a simulated Buffer with made-up data. The Buffer screen is an illustration, not a real screenshot. If it looks right, add the rest of your posts and run it again. It is safe to run as many times as you like: it never posts the same text twice.

## Make it run by itself

Do this only after step 4 worked.

- **Mac:** copy `launchd/com.example.buffer-refill.plist` to `~/Library/LaunchAgents/`, replace the two `/ABSOLUTE/PATH/TO/` with the real folder path, then run:

  ```sh
  launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.example.buffer-refill.plist
  ```

- **Linux:** add this line with `crontab -e` (adjust the path):

  ```cron
  0 8,20 * * * /usr/bin/python3 -I /path/to/buffer-queue/refill.py >> /path/to/buffer-queue/refill.log 2>&1
  ```

- **Windows:** use Task Scheduler to run `python refill.py` in this folder twice a day.

Optional: `watchdog.py` shows a notification on Mac if the refill stopped or your queue is almost empty. Run it a few times a day the same way.

## Questions and problems

**Nothing happens when I run `refill.py`.** Read the last lines it printed. `scheduled in Buffer: {...}` shows how many posts each network already has. If a network is at 10, the free-plan limit, the tool waits until some are published.

**"config not found".** Run `python3 setup.py` first.

**"Buffer answered with an error".** The API key is wrong or expired. Create a new one and run the setup again.

**Will it post something I did not write?** No. It only schedules what is in `queue.json`.

**I want to change the hours.** Open `config.json` and edit `grid` (24-hour format, in your time zone).

**I want to delete a scheduled post.** Do it in Buffer. If you also remove it from `queue.json`, it will not be scheduled again.

## Keep your account safe

- Never share `config.json`, `queue.json`, your logs or your key. If you copy this project to GitHub, they are already ignored by `.gitignore`. Still, run `git status` before each push.
- Never paste your key in a chat, issue or pull request. If it leaks, delete it in Buffer and create another.
- Use a key only for this tool, so you can delete it without breaking anything else.

## How it works inside

For people who like details. `refill.py` reads `queue.json`, asks Buffer which posts already exist (last 21 days), counts how many are scheduled per network, and creates the missing ones up to `limit` (10 by default). Overdue items move to the next free slot on your `grid`. The Buffer post id is written back to `queue.json`, which is why re-running is safe. Everything is in two small Python files with no extra libraries.

## License

MIT. Use it, change it, share it.
