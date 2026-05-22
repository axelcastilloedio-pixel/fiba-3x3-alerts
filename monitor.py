import os
import json
import smtplib
import feedparser
from email.mime.text import MIMEText
from urllib.parse import quote_plus

SEEN_FILE = "seen_events.json"

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]

SEARCHES = {
    "QUEST": 'site:play.fiba3x3.com/events QUEST FIBA 3x3',
    "LITE QUEST": 'site:play.fiba3x3.com/events "Lite Quest" FIBA 3x3'
}


def send_email(subject, body):

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        smtp.login(EMAIL_USER, EMAIL_PASS)

        smtp.send_message(msg)


def load_seen():

    try:

        with open(SEEN_FILE, "r") as f:

            return json.load(f)

    except:

        return []


def save_seen(data):

    with open(SEEN_FILE, "w") as f:

        json.dump(data, f)


def estimate_level(title):

    hard_words = [
        "Amsterdam",
        "Ub",
        "Liman",
        "Vienna",
        "Lausanne",
        "Belgrade",
        "Serbia"
    ]

    for word in hard_words:

        if word.lower() in title.lower():

            return "🔴 ALTO"

    return "🟡 MEDIO"


def estimate_opportunity(title):

    hard_words = [
        "Amsterdam",
        "Ub",
        "Liman",
        "Serbia"
    ]

    for word in hard_words:

        if word.lower() in title.lower():

            return "🔴 BAJA"

    return "🟢 INTERESANTE"


def is_valid_event(title, summary):

    text = f"{title} {summary}".lower()

    keywords = [
        "quest",
        "lite quest",
        "fiba 3x3"
    ]

    return any(word in text for word in keywords)


def search_events():

    events = []

    for category, query in SEARCHES.items():

        rss_url = (
            f"https://www.bing.com/search?"
            f"q={quote_plus(query)}&format=rss"
        )

        feed = feedparser.parse(rss_url)

        for entry in feed.entries:

            title = entry.get("title", "").strip()

            link = entry.get("link", "").strip()

            summary = entry.get("summary", "").strip()

            if "play.fiba3x3.com" not in link:
                continue

            if not is_valid_event(title, summary):
                continue

            events.append({
                "id": link,
                "name": title,
                "type": category,
                "link": link,
                "summary": summary,
                "level": estimate_level(title),
                "opportunity": estimate_opportunity(title)
            })

    unique = []

    seen_links = set()

    for e in events:

        if e["id"] not in seen_links:

            unique.append(e)

            seen_links.add(e["id"])

    return unique


def main():

    seen = load_seen()

    current = search_events()

    new_events = [
        e for e in current
        if e["id"] not in seen
    ]

    if new_events:

        body = "🏀 NUEVOS QUEST / LITE QUEST DETECTADOS\n\n"

        body += (
            "⚠️ Verificar inscripciones y nivel real.\n\n"
        )

        for e in new_events:

            body += f"{e['name']}\n"
            body += f"🏆 Tipo: {e['type']}\n"
            body += f"🔥 Nivel estimado: {e['level']}\n"
            body += f"🎯 Oportunidad: {e['opportunity']}\n"
            body += f"📝 {e['summary'][:350]}\n"
            body += f"🔗 {e['link']}\n\n"

        send_email(
            "🏀 Nuevos QUEST / LITE QUEST",
            body
        )

    current_ids = [e["id"] for e in current]

    save_seen(current_ids)


if __name__ == "__main__":
    main()
