
import requests
import feedparser
import os
import json

BOT_TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = os.environ['CHANNEL_ID']

def send_message(text):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {'chat_id': CHANNEL_ID, 'text': text}
    return requests.post(url, data=data).status_code == 200

def main():
    feed = feedparser.parse('https://news.hada.io/rss/news')
    for entry in feed.entries[:3]:
        message = f"🔥 {entry.title}\n{entry.link}"
        send_message(message)
        print(f"전송: {entry.title}")

if __name__ == "__main__":
    main()
