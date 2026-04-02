import os
import random
import smtplib
from datetime import date
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials


SHEET_NAME = "ITBS Tracker Data"
ASSETS_DIR = Path(__file__).parent / "assets" / "mail"


def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        {
            "type": os.environ["GCP_TYPE"],
            "project_id": os.environ["GCP_PROJECT_ID"],
            "private_key_id": os.environ["GCP_PRIVATE_KEY_ID"],
            "private_key": os.environ["GCP_PRIVATE_KEY"].replace("\\n", "\n"),
            "client_email": os.environ["GCP_CLIENT_EMAIL"],
            "client_id": os.environ["GCP_CLIENT_ID"],
            "auth_uri": os.environ["GCP_AUTH_URI"],
            "token_uri": os.environ["GCP_TOKEN_URI"],
            "auth_provider_x509_cert_url": os.environ["GCP_AUTH_PROVIDER_X509_CERT_URL"],
            "client_x509_cert_url": os.environ["GCP_CLIENT_X509_CERT_URL"],
            "universe_domain": os.environ.get("GCP_UNIVERSE_DOMAIN", "googleapis.com"),
        },
        scopes=scopes,
    )

    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def did_workout_today() -> bool:
    sheet = get_sheet()
    records = sheet.get_all_records()
    today = str(date.today())

    today_rows = [row for row in records if str(row.get("date")) == today]

    if not today_rows:
        return False

    # Jeśli jest choć jeden wpis z did_workout=True, uznaj dzień za zrobiony
    for row in today_rows:
        value = str(row.get("did_workout", "")).strip().lower()
        if value in {"true", "1", "yes"}:
            return True

    return False


MESSAGES = [
    {
        "subject": "Kolano pyta, czy dziś już ćwiczyłeś 👀",
        "text": "Pora coś ze sobą zrobić. Góry same się nie wejdą.",
        "html": """
        <h2>Kolano pyta, czy dziś już ćwiczyłeś 👀</h2>
        <p>Pora coś ze sobą zrobić.</p>
        <p><b>Góry same się nie wejdą.</b></p>
        """
    },
    {
        "subject": "Alarm: bez ćwiczeń będą negocjacje z kolanem 🚨",
        "text": "Zrób dziś kilka minut roboty, żeby w górach nie prowadzić rozmów kryzysowych z ITBS.",
        "html": """
        <h2>Alarm: bez ćwiczeń będą negocjacje z kolanem 🚨</h2>
        <p>Zrób dziś kilka minut roboty, żeby w górach nie prowadzić rozmów kryzysowych z ITBS.</p>
        """
    },
    {
        "subject": "Pośladek średni sam się nie zrobi 😅",
        "text": "To tylko chwila ćwiczeń. Netflix i tak poczeka.",
        "html": """
        <h2>Pośladek średni sam się nie zrobi 😅</h2>
        <p>To tylko chwila ćwiczeń.</p>
        <p><b>Netflix i tak poczeka.</b></p>
        """
    },
    {
        "subject": "Ostrzeżenie przed górami ⛰️",
        "text": "Jeśli dziś odpuścisz, jutro kolano może mieć własne zdanie.",
        "html": """
        <h2>Ostrzeżenie przed górami ⛰️</h2>
        <p>Jeśli dziś odpuścisz, jutro kolano może mieć własne zdanie.</p>
        """
    },
]


def pick_image() -> Path | None:
    if not ASSETS_DIR.exists():
        return None

    files = [p for p in ASSETS_DIR.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    if not files:
        return None

    return random.choice(files)


def send_email():
    sender = os.environ["EMAIL_SENDER"]
    receiver = os.environ["EMAIL_RECEIVER"]
    password = os.environ["EMAIL_APP_PASSWORD"]

    msg_data = random.choice(MESSAGES)
    image_path = pick_image()

    msg = MIMEMultipart("related")
    msg["Subject"] = msg_data["subject"]
    msg["From"] = sender
    msg["To"] = receiver

    alt = MIMEMultipart("alternative")
    msg.attach(alt)

    alt.attach(MIMEText(msg_data["text"], "plain", "utf-8"))

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        {msg_data["html"]}
        <p>Dziś jeszcze nie ma odhaczonego treningu w trackerze.</p>
        <p><b>Zrób ćwiczenia i uratuj wyjazd dla kolan.</b></p>
    """

    if image_path is not None:
        html += '<p><img src="cid:knee_meme" style="max-width: 700px; border-radius: 12px;"></p>'

    html += """
      </body>
    </html>
    """

    alt.attach(MIMEText(html, "html", "utf-8"))

    if image_path is not None:
        with open(image_path, "rb") as f:
            img = MIMEImage(f.read())
            img.add_header("Content-ID", "<knee_meme>")
            img.add_header("Content-Disposition", "inline", filename=image_path.name)
            msg.attach(img)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)


def main():
    if did_workout_today():
        print("Dziś ćwiczenia są już odhaczone — mail niepotrzebny.")
        return

    send_email()
    print("Mail wysłany.")


if __name__ == "__main__":
    main()
