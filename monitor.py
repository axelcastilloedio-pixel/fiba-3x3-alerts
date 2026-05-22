import os
import smtplib
import feedparser
from email.mime.text import MIMEText
from urllib.parse import quote_plus

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]

SEARCHES = {
    "QUEST": 'site:play.fiba3x3.com/events Quest FIBA 3x3',
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


def search_events():
    events = []

    for category, query in SEARCHES.items():
        rss_url = f"https://www.bing.com/search?q={quote_plus(query)}&format=rss"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip()

            events.append({
                "name": title,
                "type": category,
                "link": link,
                "summary": summary
            })

    return events


def main():
    current = search_events()

    body = "🏀 TEST BOT BING/FIBA\n\n"
    body += f"Resultados detectados: {len(current)}\n\n"

    if current:
        for e in current[:20]:
            body += f"{e['name']}\n"
            body += f"🏆 Tipo búsqueda: {e['type']}\n"
            body += f"📝 {e['summary'][:400]}\n"
            body += f"🔗 {e['link']}\n\n"
    else:
        body += "No se detectaron resultados en Bing RSS.\n"

    send_email("🏀 Test Bot Bing/FIBA", body)


if __name__ == "__main__":
    main()
