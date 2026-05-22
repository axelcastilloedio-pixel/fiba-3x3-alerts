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
    "QUEST": 'site:play.fiba3x3.com/events QUEST "2026" "FIBA 3x3"',
    "LITE QUEST": 'site:play.fiba3x3.com/events "Lite Quest" "2026" "FIBA 3x3"',
    "MAY_SEPT": 'site:play.fiba3x3.com/events Quest 2026 May OR June OR July OR August OR September'
}

HARD_SIGNALS = [
    "Amsterdam", "Ub", "Liman", "Vienna", "Lausanne",
    "Serbia", "Belgrade", "Partizan", "Riffa", "Paris"
]

GOOD_SIGNALS = [
    "Lite Quest", "Chile", "Malaysia", "Philippines",
    "Korea", "Kosovo", "Romania", "Portugal", "Greece"
]

MONTHS = [
    "May", "June", "July", "August", "September",
    "Mayo", "Junio", "Julio", "Agosto", "Septiembre"
]


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
        notes.append("Lite Quest suele ser más atacable")

    if "quest" in text.lower() and "lite" not in text.lower():
        score += 5

    if not any(m.lower() in text.lower() for m in MONTHS):
        notes.append("fecha/mes no confirmado en snippet")

    score = max(0, min(100, score))

    if score >= 75:
        label = "🟢 OPORTUNIDAD ALTA"
    elif score >= 55:
        label = "🟡 INTERESANTE"
    elif score >= 35:
        label = "🟠 DURO / REVISAR"
    else:
        label = "🔴 EVITAR SALVO MOTIVO"

    return score, label, notes


def is_valid_event(title, summary, link):
    text = f"{title} {summary}".lower()

    if "play.fiba3x3.com" not in link:
        return False

    if "quest" not in text:
        return False

    return True


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

            score, label, notes = score_event(title, summary)

            events.append({
                "id": link,
                "name": title,
                "type": category,
                "link": link,
                "summary": summary,
                "score": score,
                "label": label,
                "notes": notes
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

    if new_events:
        body = "🏀 NUEVOS QUEST / LITE QUEST DETECTADOS\n\n"
        body += "Filtro: mayo–septiembre 2026 cuando Bing lo permite.\n"
        body += "⚠️ Inscripciones/equipos aún requieren verificación manual porque FIBA bloquea GitHub.\n\n"

        for e in new_events:
            body += f"{e['name']}\n"
            body += f"🏆 Tipo búsqueda: {e['type']}\n"
            body += f"📊 Score oportunidad: {e['score']}/100\n"
            body += f"🎯 Lectura: {e['label']}\n"

            if e["notes"]:
                body += "🧠 Señales: " + "; ".join(e["notes"]) + "\n"

            body += f"📝 {e['summary'][:450]}\n"
            body += f"🔗 {e['link']}\n\n"

        send_email("🏀 Nuevas oportunidades QUEST / LITE QUEST", body)

    current_ids = [e["id"] for e in current]
    save_seen(current_ids)


if __name__ == "__main__":
    main()
