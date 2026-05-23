import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


# =========================
# CONFIGURACIÓN
# =========================

SEARCH_TERMS = [
    '"FIBA 3x3 Quest"',
    '"3x3 basketball quest"',
    '"FIBA 3x3 Challenger"',
    '"FIBA 3x3 Satellite"',
    '"3x3 basketball tournament registration"',
    '"3x3 basketball qualifier"',
    'site:fiba3x3.com quest',
    'site:play.fiba3x3.com 3x3 tournament',
]

BLACKLIST = [
    "meta quest",
    "oculus",
    "virtual reality",
    "vr headset",
    "quest diagnostics",
    "myquest",
    "appointment",
    "lab test",
    "health",
    "amazon",
    "google play",
    "app store",
    "times tables",
    "game",
]

POSITIVE_SIGNALS = [
    "fiba 3x3",
    "3x3 basketball",
    "challenger",
    "quest",
    "satellite",
    "qualifier",
    "registration",
    "teams",
    "prize",
    "tournament",
    "basketball",
]

ALLOWED_DOMAINS = [
    "fiba3x3.com",
    "play.fiba3x3.com",
    "3x3planet.com",
]


# =========================
# EMAIL
# =========================

EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


# =========================
# SERPAPI / BÚSQUEDA
# =========================

SERPAPI_KEY = os.getenv("SERPAPI_KEY")


def search_google(query):
    url = "https://serpapi.com/search"

    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "num": 10,
        "hl": "en",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    return data.get("organic_results", [])


# =========================
# FILTROS
# =========================

def is_blacklisted(text):
    text = text.lower()

    for word in BLACKLIST:
        if word in text:
            return True

    return False


def positive_score(text):
    text = text.lower()
    score = 0

    for signal in POSITIVE_SIGNALS:
        if signal in text:
            score += 1

    return score


def has_allowed_domain(url):
    url = url.lower()

    for domain in ALLOWED_DOMAINS:
        if domain in url:
            return True

    return False


def is_real_tournament_candidate(result):
    title = result.get("title", "")
    snippet = result.get("snippet", "")
    url = result.get("link", "")

    full_text = f"{title} {snippet} {url}".lower()

    if is_blacklisted(full_text):
        return False

    score = positive_score(full_text)

    if has_allowed_domain(url):
        score += 3

    if score < 3:
        return False

    return True


# =========================
# EMAIL
# =========================

def build_email(results):
    today = datetime.now().strftime("%d/%m/%Y")

    html = f"""
    <h2>🏀 Torneos 3x3 detectados - {today}</h2>
    <p>Solo se incluyen resultados que han pasado filtros mínimos de torneo real.</p>
    <hr>
    """

    for item in results:
        title = item.get("title", "Sin título")
        snippet = item.get("snippet", "Sin descripción")
        url = item.get("link", "")

        html += f"""
        <h3>{title}</h3>
        <p>{snippet}</p>
        <p><a href="{url}">{url}</a></p>
        <hr>
        """

    return html


def send_email(results):
    if not results:
        print("No hay torneos reales hoy. No se envía email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🏀 Nuevos posibles torneos reales 3x3"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    html = build_email(results)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())

    print(f"Email enviado con {len(results)} resultados.")


# =========================
# MAIN
# =========================

def main():
    if not SERPAPI_KEY:
        raise ValueError("Falta SERPAPI_KEY")

    if not EMAIL_FROM or not EMAIL_TO or not EMAIL_PASSWORD:
        raise ValueError("Faltan datos de email")

    valid_results = []
    seen_urls = set()

    for query in SEARCH_TERMS:
        print(f"Buscando: {query}")

        try:
            results = search_google(query)
        except Exception as e:
            print(f"Error buscando {query}: {e}")
            continue

        for result in results:
            url = result.get("link", "")

            if not url or url in seen_urls:
                continue

            seen_urls.add(url)

            if is_real_tournament_candidate(result):
                valid_results.append(result)

    if valid_results:
        send_email(valid_results)
    else:
        print("No hay torneos reales hoy. No se envía email.")


if __name__ == "__main__":
    main()
