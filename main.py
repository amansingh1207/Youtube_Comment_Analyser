from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import os
import uuid

app = Flask(__name__)
CORS(app)

YOUTUBE_API_KEY = "AIzaSyBMX4fEDJ0KrqT2e_LpBaYFXSgefFiPRuI"

def get_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def fetch_comments(video_id, max_results=100):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    comments = []
    next_page_token = None

    while len(comments) < max_results:
        response = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(100, max_results - len(comments)),
            pageToken=next_page_token,
            textFormat="plainText"
        ).execute()

        for item in response.get("items", []):
            comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
            comments.append(comment)

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return comments

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    url = data.get("url")
    video_id = get_video_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    comments = fetch_comments(video_id, 100)
    if not comments:
        return jsonify({"error": "No comments found"}), 404

    analyzer = SentimentIntensityAnalyzer()
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    analyzed_comments = []

    for comment in comments:
        score = analyzer.polarity_scores(comment)
        if score["compound"] >= 0.05:
            sentiment = "positive"
        elif score["compound"] <= -0.05:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        sentiment_counts[sentiment] += 1
        analyzed_comments.append({
            "text": comment,
            "sentiment": sentiment,
            "score": score["compound"]
        })

    total = len(comments)
    sentiment_percent = {
        key: round((count / total) * 100, 2)
        for key, count in sentiment_counts.items()
    }

    top_positive = sorted(
        [c for c in analyzed_comments if c["sentiment"] == "positive"],
        key=lambda x: -x["score"]
    )[:3]

    top_negative = sorted(
        [c for c in analyzed_comments if c["sentiment"] == "negative"],
        key=lambda x: x["score"]
    )[:3]

    all_words = " ".join(comments)
    wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_words)
    image_path = f"wordcloud_{uuid.uuid4().hex}.png"
    wordcloud.to_file(image_path)

    df = pd.DataFrame(analyzed_comments)
    csv_path = f"summary_{uuid.uuid4().hex}.csv"
    df.to_csv(csv_path, index=False)

    return jsonify({
        "sentiment_percent": sentiment_percent,
        "top_positive": top_positive,
        "top_negative": top_negative,
        "wordcloud_path": image_path,
        "csv_path": csv_path
    })

@app.route("/download/<filename>")
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
