from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
import os
import time

URLS = {
    "QUEST": "https://play.fiba3x3.com/events/quests",
    "LITE QUEST": "https://play.fiba3x3.com/events/litequests"
}

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


def main():
    body = "🔎 DIAGNÓSTICO FIBA PLAY\n\n"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
        )

        for category, url in URLS.items():
            body += f"===== {category} =====\n"
            body += f"URL: {url}\n\n"

            try:
                response = page.goto(url, wait_until="networkidle", timeout=60000)
                time.sleep(8)

                body += f"Status: {response.status if response else 'sin respuesta'}\n"
                body += f"Title: {page.title()}\n"
                body += f"Current URL: {page.url}\n\n"

                text = page.locator("body").inner_text(timeout=10000)
                links = page.locator("a").count()

                body += f"Número de links detectados: {links}\n\n"
                body += "Primeros 3000 caracteres visibles:\n"
                body += text[:3000]
                body += "\n\n"

            except Exception as e:
                body += f"ERROR:\n{e}\n\n"

        browser.close()

    send_email("🔎 Diagnóstico FIBA Play", body)


if __name__ == "__main__":
    main()
