from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
import smtplib
from email.mime.text import MIMEText
import os
import time

URLS = {
    "QUEST": "https://play.fiba3x3.com/events/quests",
    "LITE QUEST": "https://play.fiba3x3.com/events/litequests"
}

SEEN_FILE = "seen_events.json"

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]


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


def estimate_level(name):

    hard = [
        "Amsterdam",
        "Ub",
        "Liman",
        "Vienna",
        "Lausanne"
    ]

    for word in hard:

        if word.lower() in name.lower():
            return "🔴 ALTO"

    return "🟡 MEDIO"


def estimate_opportunity(name):

    hard = [
        "Amsterdam",
        "Ub",
        "Liman"
    ]

    for word in hard:

        if word.lower() in name.lower():
            return "🔴 BAJA"

    return "🟢 INTERESANTE"


def get_events():

    events = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        for category, url in URLS.items():

            try:

                page.goto(url, timeout=60000)

                time.sleep(5)

                html = page.content()

                soup = BeautifulSoup(html, "html.parser")

                links = soup.find_all("a")

                for link in links:

                    text = link.get_text(strip=True)

                    href = link.get("href")

                    if (
                        ("Quest" in text or "QUEST" in text)
                        and href
                        and "/events/" in href
                    ):

                        full_link = "https://play.fiba3x3.com" + href

                        events.append({
                            "name": text,
                            "type": category,
                            "link": full_link,
                            "level": estimate_level(text),
                            "opportunity": estimate_opportunity(text)
                        })

            except Exception as e:

                send_email(
                    "⚠️ Error Playwright FIBA",
                    f"No se pudo leer {url}\n\n{e}"
                )

        browser.close()

    unique = []

    names = set()

    for e in events:

        if e["name"] not in names:

            unique.append(e)

            names.add(e["name"])

    return unique


def main():

    current = get_events()

    body = "🏀 EVENTOS DETECTADOS POR EL BOT\n\n"

    if current:

        for e in current:

            body += f"{e['name']}\n"
            body += f"🏆 Tipo: {e['type']}\n"
            body += f"🔥 Nivel estimado: {e['level']}\n"
            body += f"🎯 Oportunidad: {e['opportunity']}\n"
            body += f"🔗 {e['link']}\n\n"

    else:

        body += "No se detectaron eventos.\n"

    send_email(
        "🏀 Test FIBA Bot",
        body
    )


if __name__ == "__main__":
    main()
