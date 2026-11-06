FROM python:3.11-alpine

# Build tools are needed for native packages such as TgCrypto.
RUN apk add --no-cache build-base

WORKDIR /app
COPY . ./
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

# Run the bot and HTTP server in one process so both share Pyrogram's event loop.
CMD ["python", "-u", "runner.py"]
