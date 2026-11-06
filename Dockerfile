FROM alpine:latest

# Build tools and pip are needed for Python packages with native extensions.
RUN apk add --update --no-cache python3 python3-dev py3-pip build-base multirun \
    && ln -sf python3 /usr/bin/python

WORKDIR /app
COPY . ./
RUN pip3 install --no-cache-dir --break-system-packages --upgrade pip setuptools \
    && pip3 install --no-cache-dir --break-system-packages -r requirements.txt

EXPOSE 10000

# Render provides PORT at runtime. Keep the Telegram polling bot and HTTP server
# in the same container so they share the media directory.
CMD multirun "python3 -u bot.py" "gunicorn -b 0.0.0.0:${PORT:-10000} --access-logfile - --error-logfile - app:app"
