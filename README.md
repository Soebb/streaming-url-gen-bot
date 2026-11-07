# Telegram Video Streaming Bot (Local)

Run the bot and video streaming server on your own computer. No Render account or Docker is required.

## Requirements

- Python 3.11
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Telegram API ID and API hash from [my.telegram.org](https://my.telegram.org)

## Install

Clone the repository and open a terminal in the project folder:

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows CMD**
```bat
.venv\Scripts\activate.bat
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configure

Set these environment variables before starting the app:

- `BOT_TOKEN` — token from BotFather
- `API_ID` — Telegram API ID
- `API_HASH` — Telegram API hash
- `PUBLIC_BASE_URL` — base URL used in links sent by the bot
- `MAX_VIDEO_SIZE` — optional maximum video size in bytes (default: 2 GiB)

For local use on the same computer, set `PUBLIC_BASE_URL` to:

```
http://127.0.0.1:8000
```

**Windows PowerShell example:**

```powershell
$env:BOT_TOKEN = "YOUR_BOT_TOKEN"
$env:API_ID = "YOUR_API_ID"
$env:API_HASH = "YOUR_API_HASH"
$env:PUBLIC_BASE_URL = "http://127.0.0.1:8000"
```

If you open the bot's generated links from another device, `127.0.0.1` will point to that other device, not the computer running this project. In that case, set `PUBLIC_BASE_URL` to an address reachable by that device (for example, your computer's LAN IP), and allow the server port through your firewall. For access over the internet, use a secure tunnel or a properly configured public reverse proxy.

## Start

```bash
python runner.py
```

Open the local web interface at:

```
http://127.0.0.1:8000
```

Stop the application with `Ctrl+C`.

The server binds to `127.0.0.1:8000` by default. You can override this with the optional `HOST` and `PORT` environment variables.
