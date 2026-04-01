import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="ITBS Tracker", layout="wide")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.main {
    background: linear-gradient(180deg, #071120 0%, #0c1b33 100%);
    color: #ffffff;
}

.exercise-card {
    background: #13233d;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 15px;
}

.exercise-title {
    font-size: 24px;
    font-weight: bold;
}

.badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    margin-right: 5px;
    background: #24456f;
}

.howto {
    margin-top: 10px;
    background: #0d1a2d;
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- GOOGLE SHEETS ----------------
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(creds)
    sheet = client.open("ITBS Tracker Data").sheet1
    return sheet

def load_data():
    sheet = get_sheet()
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def save_today(did_workout, pain):
    sheet = get_sheet()
    today = str(date.today())

    records = sheet.get_all_records()
    row_index = None

    for i, row in enumerate(records, start=2):
        if str(row.get("date")) == today:
            row_index = i
            break

    values = [today, did_workout, pain, ""]

    if row_index:
        sheet.update(f"A{row_index}:D{row_index}", [values])
    else:
        sheet.append_row(values)

# ---------------- EXERCISES ----------------
EXERCISES = [
    {
        "name": "Bridge / Glute bridge",
        "phase": "Faza 1",
        "category": "Siła",
        "sets": "2–3 x 10–15",
        "how_to": "Leżysz na plecach, unosisz biodra do góry, napinasz pośladki.",
        "video": "https://www.youtube.com/watch?v=m2Zx-57cSok"
    },
    {
        "name": "Clamshell",
        "phase": "Faza 1",
        "category": "Siła",
        "sets": "2–3 x 12",
        "how_to": "Leżysz na boku, unosisz kolano bez ruszania miednicy.",
        "video": "https://www.youtube.com/watch?v=EG5_gXcfozw"
    },
    {
        "name": "Side plank",
        "phase": "Faza 1",
        "category": "Core",
        "sets": "3 x 20-30s",
        "how_to": "Podpierasz się na łokciu, ciało w linii prostej.",
        "video": "https://www.youtube.com/watch?v=K2VljzCC16g"
    }
]

# ---------------- UI ----------------

st.title("Plan ćwiczeń ITBS")

# Countdown
target_date = datetime(2026, 6, 16)
days_left = (target_date - datetime.now()).days

st.info(f"⛰️ Do wyjazdu zostało: {days_left} dni")

# Check-in
st.subheader("Dzisiejszy check-in")

did = st.checkbox("Zrobiłem dziś ćwiczenia")
pain = st.slider("Poziom bólu", 0, 10, 0)

if st.button("Zapisz dzień"):
    save_today(did, pain)
    st.success("Zapisano!")

# Exercises
st.subheader("Plan ćwiczeń")

for ex in EXERCISES:
    st.markdown(f"""
    <div class="exercise-card">
        <div class="exercise-title">{ex['name']}</div>
        <div>
            <span class="badge">{ex['phase']}</span>
            <span class="badge">{ex['category']}</span>
        </div>
        <div>Dawka: {ex['sets']}</div>
        <div class="howto"><b>Jak wykonać:</b><br>{ex['how_to']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.link_button("▶ Zobacz wykonanie", ex["video"])

# Data preview
st.subheader("Twoje dane")

try:
    df = load_data()
    st.dataframe(df)
except:
    st.warning("Brak danych lub brak połączenia z Google Sheets")
