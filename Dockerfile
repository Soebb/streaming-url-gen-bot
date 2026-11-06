FROM python:3.11-alpine

# Pin Python to 3.11 for Pyrogram asyncio compatibility.
# Build tools are needed for native packages such as TgCrypto.
RUN apk add --no-cache build-base multirun

WORKDIR /app
COPY . ./
RUN pip install --no-cache-dir --upgrade pip setuptools \
    && pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
CMD multirun "python -u bot.py" "gunicorn -b :5000 --reload --access-logfile - --error-logfile - app:app"
