FROM alpine:latest

# Build tools are needed when Python packages such as TgCrypto compile native extensions.
RUN apk add --update --no-cache python3 python3-dev build-base multirun \
    && ln -sf python3 /usr/bin/python

RUN python3 -m ensurepip
WORKDIR /app
COPY . ./
RUN pip3 install --no-cache-dir --upgrade pip setuptools \
    && pip3 install --no-cache-dir -r requirements.txt

EXPOSE 10000

# Render provides PORT at runtime. Keep the Telegram polling bot and HTTP server
# in the same container so they share the persistent media directory.
CMD multirun "python3 -u bot.py" "gunicorn -b 0.0.0.0:${PORT:-10000} --access-logfile - --error-logfile - app:app"
