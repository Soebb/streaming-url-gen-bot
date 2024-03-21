import os
import requests
from urllib.parse import unquote_plus
from flask import Flask, jsonify, request
from flask import render_template
from youtube_dl import YoutubeDL
from base64 import standard_b64decode

app = Flask(__name__)


def b64_to_str(b64: str) -> str:
    bytes_b64 = b64.encode('ascii')
    bytes_str = standard_b64decode(bytes_b64)
    __str = bytes_str.decode('ascii')
    return __str

@app.route("/")
def homepage():
    return render_template("index1.html")

@app.route("/yt")
def youtube():
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
    if ("youtube.com" in video_id) and ("/" in video_id) and ("=" in video_id):
        url = video_id
    elif ("youtu.be" in video_id) and ("/" in video_id):
        url = video_id
    else:
        vid = video_id
        url = f"https://youtu.be/{vid}"
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


if __name__ == "__main__":
    app.run(debug=True)

