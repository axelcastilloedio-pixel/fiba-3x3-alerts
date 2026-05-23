import os
import json
import smtplib
import requests
import feedparser
from email.mime.text import MIMEText
from urllib.parse import quote_plus

SEEN_FILE = "seen_events.json"

EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASS = os.environ["EMAIL_PASS"]
EMAIL_TO = os.environ["EMAIL_TO"]

SEARCHES = {
    "QUEST": 'site:play.fiba3x3.com/events QUEST "FIBA 3x3"',
    "LITE QUEST": 'site:play.fiba3x3.com/events "Lite Quest" "FIBA 3x3"',
    "GLOBAL_QUEST": '"3x3 basketball" Quest "FIBA 3x3"',
    "BALKANS": '"3x3 turnir" Quest OR Bosnia OR Serbia OR Croatia',
    "RUSSIAN": '"3x3 турнир" Quest OR "ФИБА 3x3"',
    "SPANISH": '"torneo 3x3" Quest OR "FIBA 3x3"',
    "PORTUGUESE": '"torneio 3x3" Quest OR "FIBA 3x3"',
    "FRENCH": '"tournoi 3x3" Quest OR "FIBA 3x3"',
}

HARD_SIGNALS = [
    "Amsterdam",
    "Ub",
    "Liman",
    "Vienna",
    "Lausanne",
    "Serbia",
    "Belgrade",
    "Partizan",
    "Riffa",
    "Paris",
    "Ulaanbaatar",
    "Mongolia"
]

GOOD_SIGNALS = [
    "Lite Quest",
    "Chile",
    "Malaysia",
    "Philippines",
    "Korea",
    "Kosovo",
    "Romania",
    "Portugal",
    "Greece",
    "Bosnia",
    "Prnjavor",
    "Croatia"
]

MONTHS = [
    "May",
    "June",
    "July",
    "August",
    "September",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
]


# =========================
# EMAIL
# =========================

def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)


# =========================
# ARCHIVO DE EVENTOS
# =========================

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_seen(data):
    with open(SEEN_FILE, "w") as f:
        json.dump(data, f)


# =========================
# TRADUCCIÓN
# =========================

def translate_to_spanish(text):
    if not text.strip():
        return ""

    try:
        url = "https://api.mymemory.translated.net/get"

        params = {
            "q": text[:450],
            "langpair": "en|es"
        }

        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        translated = data.get("responseData", {}).get(
            "translatedText",
            ""
        )

        if translated:
            return translated

    except Exception:
        pass

    return "Traducción no disponible automáticamente."


# =========================
# SCORE
# =========================

def score_event(title, summary):
    text = f"{title} {summary}"

    score = 50
    notes = []

    for word in HARD_SIGNALS:
        if word.lower() in text.lower():
            score -= 20
            notes.append(f"riesgo alto: {word}")

    for word in GOOD_SIGNALS:
        if word.lower() in text.lower():
            score += 15
            notes.append(f"señal favorable: {word}")

    if "lite quest" in text.lower():
        score += 20
        notes.append("Lite Quest suele ser más accesible")

    if not any(m.lower() in text.lower() for m in MONTHS):
        notes.append("fecha/mes no confirmado")

    score = max(0, min(100, score))

    if score >= 75:
        label = "🟢 OPORTUNIDAD ALTA"
    elif score >= 55:
        label = "🟡 INTERESANTE"
    elif score >= 35:
        label = "🟠 REVISAR"
    else:
        label = "🔴 EVITAR"

    return score, label, notes


# =========================
# FILTRO ANTI BASURA
# =========================

def is_valid_event(title, summary, link):

    text = f"{title} {summary} {link}".lower()

    # =========================
    # BLACKLIST
    # =========================

    blacklist = [
        "meta quest",
        "quest diagnostics",
        "oculus",
        "virtual reality",
        "vr headset",
        "google play",
        "app store",
        "amazon",
        "health",
        "lab",
        "appointment",
        "times tables",
        "game",
        "youtube",
        "myquest",
    ]

    for bad in blacklist:
        if bad in text:
            return False

    # =========================
    # DOMINIOS BUENOS
    # =========================

    allowed_domains = [
        "fiba3x3.com",
        "play.fiba3x3.com",
    ]

    domain_ok = any(
        domain in link.lower()
        for domain in allowed_domains
    )

    # =========================
    # SEÑALES POSITIVAS
    # =========================

    positive_signals = [
        "fiba 3x3",
        "3x3 basketball",
        "quest",
        "lite quest",
        "challenger",
        "satellite",
        "qualifier",
        "tournament",
        "registration",
        "teams",
    ]

    score = 0

    for signal in positive_signals:
        if signal in text:
            score += 1

    if domain_ok:
        score += 2

    # =========================
    # REGLA FINAL
    # =========================

    if score < 3:
        return False

    return True


# =========================
# BÚSQUEDA
# =========================

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

            if not is_valid_event(
                title,
                summary,
                link
            ):
                continue

            score, label, notes = score_event(
                title,
                summary
            )

            original_text = f"{title}\n{summary}"

            translation = translate_to_spanish(
                original_text
            )

            events.append({
                "id": link,
                "name": title,
                "type": category,
                "link": link,
                "summary": summary,
                "translation": translation,
                "score": score,
                "label": label,
                "notes": notes
            })

    # =========================
    # ELIMINAR DUPLICADOS
    # =========================

    unique = []
    seen_links = set()

    for e in events:

        if e["id"] not in seen_links:
            unique.append(e)
            seen_links.add(e["id"])

    unique.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return unique


# =========================
# MAIN
# =========================

def main():

    seen = load_seen()

    current = search_events()

    new_events = [
        e for e in current
        if e["id"] not in seen
    ]

    # =========================
    # NO ENVIAR BASURA
    # =========================

    if not new_events:
        print("No hay torneos reales hoy.")
        return

    body = (
        "🏀 NUEVOS POSIBLES TORNEOS 3x3\n\n"
    )

    body += (
        "Resultados filtrados automáticamente.\n"
    )

    body += (
        "⚠️ Verificar inscripción, fecha y nivel.\n\n"
    )

    for e in new_events:

        body += f"{e['name']}\n"
        body += (
            f"🏆 Fuente: {e['type']}\n"
        )

        body += (
            f"📊 Score: {e['score']}/100\n"
        )

        body += (
            f"🎯 Lectura: {e['label']}\n"
        )

        if e["notes"]:
            body += (
                "🧠 Señales: "
                + "; ".join(e["notes"])
                + "\n"
            )

        body += (
            f"\n🌍 Original:\n"
            f"{e['summary'][:500]}\n"
        )

        body += (
            f"\n🇪🇸 Traducción:\n"
            f"{e['translation'][:700]}\n"
        )

        body += (
            f"\n🔗 {e['link']}\n\n"
        )

        body += (
            "-----------------------------\n\n"
        )

    send_email(
        "🏀 Nuevos torneos 3x3 detectados",
        body
    )

    current_ids = [e["id"] for e in current]

    save_seen(current_ids)


if __name__ == "__main__":
    main()
