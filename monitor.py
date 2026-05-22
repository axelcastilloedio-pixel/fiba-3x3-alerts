import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os

URLS = [
    "https://play.fiba3x3.com/events/quests",
    "https://play.fiba3x3.com/events/litequests"
]

SEEN_FILE = "seen_events.json"

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)

def get_events():
    events = []

    for url in URLS:
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")

        links = soup.find_all("a")

        for link in links:
            text = link.get_text(strip=True)

            if "Quest" in text or "QUEST" in text:
                events.append(text)

    return list(set(events))

def send_email(new_events):
    body = "Nuevos torneos detectados:\n\n"

    for event in new_events:
        body += f"- {event}\n"

    msg = MIMEText(body)

    msg["Subject"] = "🏀 Nuevos QUEST / LITE QUEST FIBA 3x3"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def main():
    seen = load_seen()
    current = get_events()

    new_events = [e for e in current if e not in seen]

    if new_events:
    send_email(new_events)
        

    save_seen(current)

if __name__ == "__main__":
    main()
