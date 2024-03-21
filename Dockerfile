FROM alpine:latest
RUN apk add --update --no-cache python3 multirun && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
WORKDIR /app
COPY . ./
RUN pip3 install --no-cache --upgrade pip setuptools && pip3 install -r requirements.txt
CMD
