import requests
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os

URLS = {
    "QUEST": "https://play.fiba3x3.com/events/quests",
    "LITE QUEST": "https://play.fiba3x3.com/events/litequests"
}

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

def estimate_level(name):
    elite_keywords = ["Amsterdam", "Ub", "Liman", "Vienna", "Lausanne"]

    for word in elite_keywords:
        if word.lower() in name.lower():
            return "🔴 ALTO"

    return "🟡 MEDIO"

def estimate_opportunity(name):
    hard_keywords = ["Amsterdam", "Ub", "Liman"]

    for word in hard_keywords:
        if word.lower() in name.lower():
            return "🔴 BAJA"

    return "🟢 INTERESANTE"

def get_events():
    events = []

    for category, url in URLS.items():
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")

        links = soup.find_all("a")

        for link in links:
            text = link.get_text(strip=True)

            if "Quest" in text or "QUEST" in text:

                href = link.get("href")

                if href and "/events/" in href:

                    full_link = "https://play.fiba3x3.com" + href

                    events.append({
                        "name": text,
                        "type": category,
                        "link": full_link,
                        "level": estimate_level(text),
                        "opportunity": estimate_opportunity(text)
                    })

    unique = []

    names = set()

    for e in events:
        if e["name"] not in names:
            unique.append(e)
            names.add(e["name"])

    return unique

def send_email(new_events):

    body = "🏀 NUEVOS TORNEOS FIBA 3x3 DETECTADOS\n\n"

    for e in new_events:

        body += f"{e['name']}\n"
        body += f"🏆 Tipo: {e['type']}\n"
        body += f"🔥 Nivel estimado: {e['level']}\n"
        body += f"🎯 Oportunidad: {e['opportunity']}\n"
        body += f"🔗 {e['link']}\n\n"

    msg = MIMEText(body)

    msg["Subject"] = "🏀 Nuevos QUEST / LITE QUEST"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def main():

    seen = load_seen()

    current = get_events()

    current_names = [e["name"] for e in current]

    new_events = [e for e in current if e["name"] not in seen]

    if new_events:
    send_email(new_events)

    save_seen(current_names)


if __name__ == "__main__":
    main()
