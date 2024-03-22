import os
import requests
from urllib.parse import unquote_plus
from flask import Flask, jsonify, request
from flask import render_template
from yt_dlp import YoutubeDL
from base64 import standard_b64decode

app = Flask(__name__)


def b64_to_str(b64: str) -> str:
    bytes_b64 = b64.encode('ascii')
    bytes_str = standard_b64decode(bytes_b64)
    __str = bytes_str.decode('ascii')
    return __str

@app.route("/")
def homepage():
    return "Hello.."

@app.route("/yt")
def youtube():
    try:
        url = request.args['id']
    except Exception as e:
        edata = "Please parse ?id= when calling the api"
        return edata

    with YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
    video_name = info_dict['title']
    videos = [ {"format": format["height"], "url": format["url"]} for format in info_dict["formats"] if format["format_id"] in ["18", "22"] ]
    # captions = info_dict["aut|safeomatic_captions"]
    captions = []
    video_captions = [ {caption: captions[caption][-1]["url"]} for caption in captions]
    return render_template(
        "yt_template.html",
        video_name=video_name,
        videos=videos,
        video_captions=video_captions)


@app.route("/jw")
def jw_payer():
    try:
        video_id = request.args['id']
    except Exception as e:
        edata = "Please parse ?id= when calling the api"
        return edata
    try:
        encypted = request.args['en']
    except Exception as e:
        encypted = 1
    if encypted == "0":
        video_id = video_id
    else:
        try:
            video_id = b64_to_str(video_id)
        except:
            return "<font color=red size=15>Wrong Video ID</font> <br> ask at @JV_Community in Telegram"
    jw_url = "https://cdn.jwplayer.com/v2/media"
    video_response = requests.get(f"{jw_url}/{video_id}")
    if video_response.status_code != 200:
        return "<font color=red size=20>Wrong Video ID</font>"
    video = video_response.json()
    video_url = video["playlist"][0]["sources"][0]["file"]
    track_url = video["playlist"][0]["tracks"][0]["file"]
    return render_template(
        "m3u8.html",
        video_url=video_url,
        track_url=track_url,
    )

@app.route("/play")
def play():
    try:
        video_id = request.args['id']
    except Exception as e:
        edata = "Please parse ?id= when calling the api"
        return edata
    try:
        encypted = request.args['en']
    except Exception as e:
        encypted = 1
    if encypted == "0":
        video_id = video_id
    else:
        try:
            video_id = b64_to_str(video_id)
        except:
            return "<font color=red size=15>Wrong Video ID</font> <br> sorry"
    video_url = video_id
    track_url = video_id
    video_name = video_id.split("/")[-1]
    return render_template(
        "temp.html",
        type="jw",
        video_name=unquote_plus(video_name),
        video_url=video_url,
        track_url=track_url,
    )

@app.route("/m3u8")
def m3u8():
    try:
        video_url = request.args['id']
    except Exception as e:
        edata = "Please parse ?id= when calling the api"
        return edata
    try:
        encypted = request.args['en']
    except Exception as e:
        encypted = 1
    if encypted == "0":
        video_url = video_url
    else:
        try:
            video_url = b64_to_str(video_url)
        except:
            return "<font color=red size=15>Wrong Video ID</font> <br> sorry"
    return render_template(
        "m3u8.html",
        video_url=video_url,
        track_url=video_url
    )
