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
    "FIBA QUEST": 'site:play.fiba3x3.com/events Quest "FIBA 3x3"',
    "FIBA LITE QUEST": 'site:play.fiba3x3.com/events "Lite Quest"',
    "FIBA CHALLENGER": 'site:play.fiba3x3.com/events Challenger "FIBA 3x3"',
    "FIBA SATELLITE": 'site:play.fiba3x3.com/events Satellite "FIBA 3x3"',
    "GLOBAL QUEST": '"3x3 basketball" "Quest" "FIBA 3x3" 2026',
    "SPANISH": '"torneo 3x3" "Quest" "FIBA 3x3" 2026',
    "PORTUGUESE": '"torneio 3x3" "Quest" "FIBA 3x3" 2026',
    "FRENCH": '"tournoi 3x3" "Quest" "FIBA 3x3" 2026',
    "BALKANS": '"3x3 turnir" "Quest" "FIBA 3x3" 2026',
}

BLACKLIST = [
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

STRONG_SIGNALS = [
    "fiba 3x3",
    "play.fiba3x3.com",
    "lite quest",
    "challenger",
    "satellite",
    "qualifier",
    "registration",
    "teams",
    "tournament",
    "3x3 basketball",
]

FUTURE_SIGNALS = [
    "2026",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
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
    "Croatia",
]

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
    "Mongolia",
]


def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
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


def translate_to_spanish(text):
    if not text.strip():
        return ""

    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text[:450],
            "langpair": "en|es",
        }

        response = requests.get(url, params=params, timeout=20)
        data = response.json()

        translated = data.get("responseData", {}).get("translatedText", "")

        if translated:
            return translated

    except Exception:
        pass

    return "Traducción no disponible automáticamente."


def contains_any(text, words):
    text = text.lower()
    return any(word.lower() in text for word in words)


def count_signals(text, words):
    text = text.lower()
    total = 0

    for word in words:
        if word.lower() in text:
            total += 1

    return total


def is_valid_event(title, summary, link):
    text = f"{title} {summary} {link}".lower()

    if contains_any(text, BLACKLIST):
        return False

    is_fiba_domain = (
        "play.fiba3x3.com" in link.lower()
        or "fiba3x3.com" in link.lower()
    )

    strong_score = count_signals(text, STRONG_SIGNALS)
    has_future_signal = contains_any(text, FUTURE_SIGNALS)

    # Regla principal:
    # 1) Si tiene fecha futura y señales fuertes, pasa.
    if has_future_signal and strong_score >= 2:
        return True

    # 2) Si viene de FIBA/play.fiba3x3 y tiene señales fuertes, pasa aunque Bing no muestre fecha.
    if is_fiba_domain and strong_score >= 2:
        return True

    # 3) Todo lo demás se descarta.
    return False


def score_event(title, summary, link):
    text = f"{title} {summary} {link}"

    score = 50
    notes = []

    if "play.fiba3x3.com" in link.lower():
        score += 25
        notes.append("dominio oficial FIBA/play.fiba3x3")

    if contains_any(text, FUTURE_SIGNALS):
        score += 15
        notes.append("fecha futura detectada")
    else:
        notes.append("fecha no visible en Bing; revisar enlace")

    for word in GOOD_SIGNALS:
        if word.lower() in text.lower():
            score += 10
            notes.append(f"señal favorable: {word}")

    for word in HARD_SIGNALS:
        if word.lower() in text.lower():
            score -= 15
            notes.append(f"posible nivel alto: {word}")

    if "lite quest" in text.lower():
        score += 20
        notes.append("Lite Quest suele ser más accesible")

    if "challenger" in text.lower():
        score -= 10
        notes.append("Challenger suele tener nivel alto")

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


def search_events():
    events = []

    for category, query in SEARCHES.items():
        rss_url = f"https://www.bing.com/search?q={quote_plus(query)}&format=rss"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip()

            if not is_valid_event(title, summary, link):
                continue

            score, label, notes = score_event(title, summary, link)

            original_text = f"{title}\n{summary}"
            translation = translate_to_spanish(original_text)

            events.append({
                "id": link,
                "name": title,
                "type": category,
                "link": link,
                "summary": summary,
                "translation": translation,
                "score": score,
                "label": label,
                "notes": notes,
            })

    unique = []
    seen_links = set()

    for e in events:
        if e["id"] not in seen_links:
            unique.append(e)
            seen_links.add(e["id"])

    unique.sort(key=lambda x: x["score"], reverse=True)

    return unique


def main():
    seen = load_seen()
    current = search_events()

    new_events = [
        e for e in current
        if e["id"] not in seen
    ]

    if not new_events:
        print("No hay nuevos torneos 3x3 válidos hoy.")
        save_seen([e["id"] for e in current])
        return

    body = "🏀 NUEVOS POSIBLES TORNEOS 3x3\n\n"
    body += "Filtro equilibrado: prioriza eventos futuros, pero permite enlaces oficiales FIBA aunque Bing no muestre fecha.\n"
    body += "⚠️ Verificar inscripción, fecha, ciudad, país y nivel antes de decidir.\n\n"

    for e in new_events:
        body += f"{e['name']}\n"
        body += f"🏆 Fuente: {e['type']}\n"
        body += f"📊 Score: {e['score']}/100\n"
        body += f"🎯 Lectura: {e['label']}\n"

        if e["notes"]:
            body += "🧠 Señales: " + "; ".join(e["notes"]) + "\n"

        body += f"\n🌍 Original:\n{e['summary'][:500]}\n"
        body += f"\n🇪🇸 Traducción:\n{e['translation'][:700]}\n"
        body += f"\n🔗 {e['link']}\n\n"
        body += "-----------------------------\n\n"

    send_email(
        "🏀 Nuevos torneos 3x3 detectados",
        body,
    )

    current_ids = [e["id"] for e in current]
    save_seen(current_ids)


if __name__ == "__main__":
    main()
