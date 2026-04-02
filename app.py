import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date

# =========================
# KONFIG
# =========================
st.set_page_config(page_title="ITBS Tracker", page_icon="🏔️", layout="wide")

TARGET_DATE = date(2026, 6, 16)
SHEET_NAME = "ITBS Tracker Data"

# =========================
# GOOGLE SHEETS
# =========================
def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def load_data():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()

        if not records:
            return pd.DataFrame(columns=["date", "did_workout", "pain_level", "notes"])

        df = pd.DataFrame(records)

        df["did_workout"] = df["did_workout"].astype(str).str.lower().isin(["true", "1", "yes"])
        df["pain_level"] = pd.to_numeric(df["pain_level"], errors="coerce")

        return df
    except:
        return pd.DataFrame(columns=["date", "did_workout", "pain_level", "notes"])


def save_today(did_workout, pain, notes):
    sheet = get_sheet()
    today = str(date.today())

    records = sheet.get_all_records()
    row_index = None

    for i, row in enumerate(records, start=2):
        if str(row.get("date")) == today:
            row_index = i
            break

    values = [today, did_workout, pain, notes]

    if row_index is not None:
        sheet.update(range_name=f"A{row_index}:D{row_index}", values=[values])
    else:
        sheet.append_row(values)

    return True


# =========================
# PLAN
# =========================
PHASES = {
    "Faza 1": "Aktywacja i zmniejszenie bólu",
    "Faza 2": "Stabilność i kontrola",
    "Faza 3": "Powrót do aktywności"
}

EXERCISES = {
    "Faza 1": [
        "Bridge",
        "Clamshell",
        "Side plank"
    ],
    "Faza 2": [
        "Monster walk",
        "Step-up",
        "Single-leg balance"
    ],
    "Faza 3": [
        "Lunges",
        "Single-leg deadlift",
        "Walking uphill"
    ]
}


def get_phase():
    days_left = (TARGET_DATE - date.today()).days

    if days_left > 70:
        return "Faza 1"
    elif days_left > 35:
        return "Faza 2"
    else:
        return "Faza 3"


# =========================
# APP
# =========================
st.title("🏔️ ITBS Tracker")

days_left = (TARGET_DATE - date.today()).days
phase = get_phase()

col1, col2 = st.columns(2)

with col1:
    st.metric("Dni do wyjazdu", days_left)

with col2:
    st.metric("Aktualna faza", phase)

st.info("Ćwicz 3–4 razy w tygodniu. Nie musisz robić wszystkiego codziennie.")

# =========================
# PLAN NA DZIŚ
# =========================
st.subheader("Dziś zrób:")

for ex in EXERCISES[phase]:
    st.write(f"• {ex}")

# =========================
# CHECK-IN
# =========================
st.subheader("Dzisiejszy check-in")

did = st.checkbox("Zrobiłem ćwiczenia")
pain = st.slider("Poziom bólu", 0, 10, 0)
notes = st.text_area("Notatka")

if st.button("Zapisz dzień"):
    try:
        save_today(did, pain, notes)
        st.success("Zapisano do Google Sheets")
        st.rerun()
    except Exception as e:
        st.error(f"Błąd zapisu: {str(e)}")


# =========================
# DANE
# =========================
st.subheader("Twoje dane")

df = load_data()

if not df.empty:
    st.dataframe(df.sort_values("date", ascending=False))
else:
    st.warning("Brak danych")
