FROM python:3.11-alpine

# Pyrogram currently relies on asyncio event-loop behavior that changed in Python 3.14.
# Pin Python to 3.11 and install build tools for native packages such as TgCrypto.
RUN apk add --no-cache build-base multirun

WORKDIR /app
COPY . ./
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

# Render provides PORT at runtime. Keep the Telegram polling bot and HTTP server
# in the same container so they share the media directory.
CMD multirun "python -u bot.py" "gunicorn -b 0.0.0.0:${PORT:-10000} --access-logfile - --error-logfile - app:app"
