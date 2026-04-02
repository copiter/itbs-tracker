import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date

# =========================
# KONFIG
# =========================
st.set_page_config(
    page_title="ITBS Tracker",
    page_icon="🏔️",
    layout="wide",
)

TARGET_DATE = date(2026, 6, 16)
SHEET_NAME = "ITBS Tracker Data"

# =========================
# STYLE
# =========================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #08111f 0%, #0c1a31 50%, #102344 100%);
    color: #eaf2ff;
}

.block-container {
    max-width: 1100px;
    padding-top: 2rem;
}

h1, h2, h3 {
    color: #ffffff !important;
}

.card {
    background: rgba(255,255,255,0.05);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

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
# PLAN LOGIKA
# =========================
def get_phase():
    days_left = (TARGET_DATE - date.today()).days

    if days_left > 70:
        return "Faza 1"
    elif days_left > 35:
        return "Faza 2"
    else:
        return "Faza 3"


PHASE_INFO = {
    "Faza 1": "Aktywacja i zmniejszenie bólu",
    "Faza 2": "Stabilność i kontrola",
    "Faza 3": "Powrót do aktywności"
}

EXERCISES = {
    "Faza 1": [
        "Bridge (2–3x 12 powtórzeń)",
        "Clamshell (2–3x 12/strona)",
        "Side plank (3x 20–30s)",
    ],
    "Faza 2": [
        "Monster walk (2–3 serie)",
        "Step-up (2–3x 10/strona)",
        "Single-leg balance (3x 30s)",
    ],
    "Faza 3": [
        "Lunges (2–3x 8/strona)",
        "Single-leg deadlift (2–3x 8)",
        "Walking uphill (10–20 min)",
    ],
}

# =========================
# HEADER
# =========================
st.title("🏔️ ITBS Tracker")

days_left = (TARGET_DATE - date.today()).days
phase = get_phase()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Dni do wyjazdu", max(days_left, 0))

with col2:
    st.metric("Aktualna faza", phase)

with col3:
    st.metric("Plan", PHASE_INFO[phase])

st.info("Ćwicz 3–4 razy w tygodniu. Nie rób wszystkiego codziennie.")

# =========================
# PLAN NA DZIŚ
# =========================
st.subheader("Dziś zrób:")

for ex in EXERCISES[phase]:
    st.markdown(f"• {ex}")

# =========================
# CHECK-IN
# =========================
st.subheader("Dzisiejszy check-in")

did = st.checkbox("Zrobiłem dziś ćwiczenia")
pain = st.slider("Poziom bólu", 0, 10, 0)
notes = st.text_area("Notatka (opcjonalnie)")

if st.button("Zapisz dzień"):
    try:
        save_today(did, pain, notes)
        st.success("Dzień zapisany ✔")
        st.rerun()
    except Exception as e:
        st.error(f"Błąd zapisu: {str(e)}")

# =========================
# DANE
# =========================
st.subheader("Twoje dane")

df = load_data()

if not df.empty:
    st.dataframe(df.sort_values("date", ascending=False), use_container_width=True)

    st.markdown("### Podsumowanie")

    total = len(df)
    done = df["did_workout"].sum()
    avg_pain = round(df["pain_level"].mean(), 1) if df["pain_level"].notna().any() else "-"

    c1, c2, c3 = st.columns(3)

    c1.metric("Wpisy", total)
    c2.metric("Ćwiczone dni", int(done))
    c3.metric("Średni ból", avg_pain)
else:
    st.warning("Brak danych")

# =========================
# STOPKA
# =========================
st.markdown("""
---
Najważniejsze: regularność > ilość.  
3–4 treningi tygodniowo wystarczą, żeby zrobić progres przed wyjazdem.
""")
