import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date, datetime

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
html, body, [class*="css"] {
    color: #eef4ff;
}

.stApp {
    background: linear-gradient(180deg, #08111f 0%, #0c1a31 45%, #102344 100%);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1200px;
}

h1, h2, h3 {
    color: #ffffff !important;
}

.card {
    background: rgba(18, 35, 61, 0.88);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.18);
}

.metric-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 18px;
    padding: 16px;
    text-align: center;
}

.exercise-card {
    background: rgba(18, 35, 61, 0.94);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 16px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.18);
}

.exercise-title {
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 12px;
}

.badge {
    display: inline-block;
    padding: 7px 12px;
    border-radius: 999px;
    margin-right: 8px;
    margin-bottom: 10px;
    font-size: 13px;
    font-weight: 700;
    background: #22456f;
    color: #eaf2ff;
}

.section-note {
    background: rgba(255,255,255,0.05);
    border-left: 4px solid #5aa0ff;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 10px;
    margin-bottom: 14px;
    color: #e8f1ff;
}

.small-muted {
    color: #b8c8e6;
    font-size: 14px;
}

.plan-box {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px;
    padding: 16px;
    margin-bottom: 12px;
}

.phase-box {
    background: rgba(255,255,255,0.04);
    border-radius: 18px;
    padding: 18px;
    border: 1px solid rgba(255,255,255,0.08);
}

div[data-testid="stMetricValue"] {
    color: #ffffff;
}

div[data-testid="stMetricLabel"] {
    color: #cfe0ff;
}

div[data-testid="stDataFrame"] {
    background: white;
    border-radius: 12px;
    padding: 8px;
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
    sheet = client.open(SHEET_NAME).sheet1
    return sheet


def load_data():
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=["date", "did_workout", "pain_level", "notes"])
        df = pd.DataFrame(records)

        if "date" in df.columns:
            df["date"] = df["date"].astype(str)

        if "did_workout" in df.columns:
            df["did_workout"] = df["did_workout"].astype(str).str.lower().isin(["true", "1", "yes"])

        if "pain_level" in df.columns:
            df["pain_level"] = pd.to_numeric(df["pain_level"], errors="coerce")

        if "notes" not in df.columns:
            df["notes"] = ""

        return df
    except Exception:
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

    if row_index:
        sheet.update(f"A{row_index}:D{row_index}", [values])
    else:
        sheet.append_row(values)


# =========================
# PLAN ĆWICZEŃ
# =========================
PHASES = {
    "Faza 1": {
        "title": "Aktywacja i uspokojenie przeciążenia",
        "goal": "Zmniejszyć dolegliwości, pobudzić pośladek średni i ustabilizować biodro.",
        "frequency": "3–4 treningi tygodniowo",
        "comment": "Nie robisz wszystkiego codziennie. W tej fazie liczy się regularność i dobra technika."
    },
    "Faza 2": {
        "title": "Stabilność i kontrola w ruchu",
        "goal": "Poprawić kontrolę miednicy i biodra przy staniu, chodzeniu i prostych ruchach jednonóż.",
        "frequency": "3–4 treningi tygodniowo",
        "comment": "Tu wchodzą bardziej funkcjonalne ćwiczenia, ale nadal bez przesady z objętością."
    },
    "Faza 3": {
        "title": "Powrót do większego obciążenia",
        "goal": "Przygotować ciało do bardziej wymagającego wysiłku i wyjazdu w góry.",
        "frequency": "3 treningi tygodniowo + lekka aktywność",
        "comment": "Nie chodzi o robienie wszystkiego codziennie. Chodzi o stopniowy progres bez podbijania bólu."
    }
}


EXERCISES = [
    {
        "name": "Bridge / Glute bridge",
        "phase": "Faza 1",
        "category": "Siła",
        "sets": "2–3 serie x 10–15 powtórzeń",
        "purpose": "Aktywacja pośladków i poprawa kontroli miednicy.",
        "how_to": "Połóż się na plecach, ugnij kolana i oprzyj stopy o podłoże. Napnij brzuch i pośladki, unieś biodra do góry, aż tułów i uda będą w jednej linii. Opuść powoli.",
        "comment": "To ćwiczenie możesz robić regularnie przez dłuższy czas jako baza.",
        "video": "https://www.youtube.com/watch?v=m2Zx-57cSok",
    },
    {
        "name": "Clamshell",
        "phase": "Faza 1",
        "category": "Siła",
        "sets": "2–3 serie x 12–15 powtórzeń na stronę",
        "purpose": "Wzmacnianie pośladka średniego, który często jest kluczowy przy ITBS.",
        "how_to": "Połóż się na boku z ugiętymi kolanami. Stopy trzymaj razem. Unieś górne kolano do góry bez rotowania miednicy do tyłu.",
        "comment": "Jeśli czujesz bardziej plecy niż bok pośladka, zwolnij ruch i zmniejsz zakres.",
        "video": "https://www.youtube.com/watch?v=EG5_gXcfozw",
    },
    {
        "name": "Side plank",
        "phase": "Faza 1",
        "category": "Core",
        "sets": "3 serie x 20–30 sekund",
        "purpose": "Stabilizacja tułowia i biodra.",
        "how_to": "Oprzyj się na łokciu i zewnętrznej krawędzi stopy lub na kolanie w łatwiejszej wersji. Utrzymaj ciało w jednej linii.",
        "comment": "Nie chodzi o rekord czasu, tylko o spokojne, równe napięcie.",
        "video": "https://www.youtube.com/watch?v=K2VljzCC16g",
    },
    {
        "name": "Side-lying hip abduction",
        "phase": "Faza 1",
        "category": "Siła",
        "sets": "2–3 serie x 10–15 powtórzeń na stronę",
        "purpose": "Wzmacnianie odwodzicieli biodra.",
        "how_to": "Połóż się na boku, dolna noga lekko ugięta. Górną nogę unoś prosto lekko do tyłu, bez rotowania stopy do góry.",
        "comment": "Ma palić w bocznej części pośladka, nie w lędźwiach.",
        "video": "https://www.youtube.com/watch?v=jgh6sGwtTwk",
    },
    {
        "name": "Single-leg balance",
        "phase": "Faza 2",
        "category": "Stabilizacja",
        "sets": "3 serie x 20–40 sekund na stronę",
        "purpose": "Poprawa równowagi i kontroli biodra w staniu na jednej nodze.",
        "how_to": "Stań na jednej nodze, utrzymaj miednicę równo, nie zapadaj kolana do środka.",
        "comment": "Jak będzie za łatwo, możesz dodać lekki ruch ręką albo dotykanie punktów stopą drugiej nogi.",
        "video": "https://www.youtube.com/watch?v=u08lo0bESJc",
    },
    {
        "name": "Monster walks",
        "phase": "Faza 2",
        "category": "Siła / chód",
        "sets": "2–3 serie x 10–15 kroków w każdą stronę",
        "purpose": "Wzmacnianie pośladków w bardziej funkcjonalnym ustawieniu.",
        "how_to": "Załóż miniband nad kolana lub na kostki, zejdź lekko w półprzysiad i idź bokiem lub po skosie, utrzymując napięcie gumy.",
        "comment": "Ma być wolno i pod kontrolą, nie szybkie dreptanie.",
        "video": "https://www.youtube.com/watch?v=Q1r0WmCqG4k",
    },
    {
        "name": "Step-up",
        "phase": "Faza 2",
        "category": "Funkcjonalne",
        "sets": "2–3 serie x 8–12 powtórzeń na stronę",
        "purpose": "Przygotowanie pod schody i teren.",
        "how_to": "Wejdź jedną nogą na podwyższenie, dociśnij stopę i wyprostuj biodro bez odbijania się z drugiej nogi.",
        "comment": "Pilnuj, żeby kolano nie uciekało do środka.",
        "video": "https://www.youtube.com/watch?v=aajhW7DD1EA",
    },
    {
        "name": "Sit-to-stand / squat to chair",
        "phase": "Faza 2",
        "category": "Funkcjonalne",
        "sets": "2–3 serie x 8–12 powtórzeń",
        "purpose": "Budowa siły i kontroli w prostym wzorcu przysiadu.",
        "how_to": "Usiądź na krześle i wstań z kontrolą, dociskając stopy do podłogi. Ruch spokojny, bez zapadania kolan.",
        "comment": "To ma być czyste technicznie, nie maksymalnie ciężko.",
        "video": "https://www.youtube.com/watch?v=1xMaFs0L3ao",
    },
    {
        "name": "Reverse lunge",
        "phase": "Faza 3",
        "category": "Siła funkcjonalna",
        "sets": "2–3 serie x 6–10 powtórzeń na stronę",
        "purpose": "Przygotowanie do bardziej wymagającego ruchu jednonóż.",
        "how_to": "Zrób krok w tył i zejdź do wykroku, utrzymując stabilne biodro i kolano z przodu.",
        "comment": "Jeśli ból się nasila, wróć do ćwiczeń z fazy 2.",
        "video": "https://www.youtube.com/watch?v=wrwwXE_x-pQ",
    },
    {
        "name": "Single-leg Romanian deadlift (łatwa wersja)",
        "phase": "Faza 3",
        "category": "Stabilizacja / siła",
        "sets": "2–3 serie x 6–10 powtórzeń na stronę",
        "purpose": "Kontrola biodra, tyłu uda i stabilizacja jednonóż.",
        "how_to": "Stań na jednej nodze, pochyl tułów do przodu i wyprostuj drugą nogę w tył. Biodra trzymaj równo.",
        "comment": "Na początku możesz podpierać się jedną ręką o ścianę.",
        "video": "https://www.youtube.com/watch?v=2SHsk9AzdjA",
    },
    {
        "name": "Marching / uphill walking",
        "phase": "Faza 3",
        "category": "Przygotowanie do wyjazdu",
        "sets": "10–20 minut spokojnej pracy",
        "purpose": "Stopniowy powrót do bardziej specyficznego wysiłku pod góry.",
        "how_to": "Spokojny marsz, lekki teren, schody albo niewielkie podejścia bez prowokowania bólu.",
        "comment": "Dodawaj dopiero wtedy, gdy wcześniejsze fazy są dobrze tolerowane.",
        "video": "https://www.youtube.com/results?search_query=uphill+walking+hip+stability",
    },
]


# =========================
# LOGIKA PLANU
# =========================
def get_days_left():
    return (TARGET_DATE - date.today()).days


def get_current_phase():
    days_left = get_days_left()

    # Im bliżej wyjazdu, tym dalsza faza
    if days_left > 70:
        return "Faza 1"
    elif days_left > 35:
        return "Faza 2"
    else:
        return "Faza 3"


def get_phase_exercises(phase_name):
    return [ex for ex in EXERCISES if ex["phase"] == phase_name]


def get_today_plan(phase_name):
    phase_exercises = get_phase_exercises(phase_name)

    if phase_name == "Faza 1":
        return phase_exercises[:4]
    if phase_name == "Faza 2":
        return phase_exercises[:4]
    return phase_exercises[:3]


def summarize_data(df):
    if df.empty:
        return 0, 0, None

    total_entries = len(df)
    completed = int(df["did_workout"].sum()) if "did_workout" in df.columns else 0

    pain_avg = None
    if "pain_level" in df.columns and df["pain_level"].notna().any():
        pain_avg = round(df["pain_level"].dropna().mean(), 1)

    return total_entries, completed, pain_avg


# =========================
# DANE
# =========================
df = load_data()
current_phase = get_current_phase()
phase_info = PHASES[current_phase]
today_plan = get_today_plan(current_phase)
days_left = get_days_left()
total_entries, completed_entries, pain_avg = summarize_data(df)

progress_percent = max(0, min(100, int((completed_entries / max(1, 24)) * 100)))


# =========================
# HEADER
# =========================
st.title("🏔️ ITBS Tracker")
st.caption("Plan przygotowania pod wyjazd z odliczaniem, zapisem ćwiczeń i prostym monitoringiem progresu.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Dni do wyjazdu", max(days_left, 0))

with col2:
    st.metric("Aktualna faza", current_phase)

with col3:
    st.metric("Zapisane dni", total_entries)

with col4:
    st.metric("Dni z ćwiczeniami", completed_entries)

st.progress(progress_percent / 100)
st.caption(f"Orientacyjny progres regularności: {progress_percent}%")

st.markdown(f"""
<div class="section-note">
<b>Jak czytać ten plan?</b><br>
Nie chodzi o robienie wszystkich ćwiczeń codziennie i w dowolnej ilości.<br>
Najlepiej celować w <b>3–4 treningi tygodniowo</b>, a w dni bez treningu możesz zrobić lekki spacer, mobilność albo odpoczynek.<br>
Plan zmienia się z czasem: teraz aplikacja pokazuje Ci <b>{current_phase}</b>.
</div>
""", unsafe_allow_html=True)


# =========================
# FAZA
# =========================
st.subheader("Aktualna faza planu")

st.markdown(f"""
<div class="phase-box">
    <div class="exercise-title">{phase_info["title"]}</div>
    <div><span class="badge">{current_phase}</span></div>
    <p><b>Cel:</b> {phase_info["goal"]}</p>
    <p><b>Częstotliwość:</b> {phase_info["frequency"]}</p>
    <p class="small-muted">{phase_info["comment"]}</p>
</div>
""", unsafe_allow_html=True)


# =========================
# PLAN NA DZIŚ
# =========================
st.subheader("Dziś zrób to")

for idx, ex in enumerate(today_plan, start=1):
    st.markdown(f"""
    <div class="plan-box">
        <b>{idx}. {ex["name"]}</b><br>
        <span class="small-muted">{ex["sets"]}</span><br>
        {ex["purpose"]}
    </div>
    """, unsafe_allow_html=True)

st.info(
    "To jest propozycja dzisiejszego zestawu. Nie musisz robić wszystkich ćwiczeń z całej aplikacji każdego dnia."
)


# =========================
# CHECK-IN
# =========================
st.subheader("Dzisiejszy check-in")

with st.container():
    c1, c2 = st.columns([1, 1])

    with c1:
        did = st.checkbox("Zrobiłem dziś ćwiczenia")
        pain = st.slider("Poziom bólu dziś", 0, 10, 0)

    with c2:
        notes = st.text_area(
            "Notatka",
            placeholder="Np. clamshell był OK, step-up lekko ciągnął po zewnętrznej stronie kolana, spacer bez bólu...",
            height=120
        )

if st.button("Zapisz dzień", use_container_width=True):
    try:
        save_today(did, pain, notes)
        st.success("Dzień został zapisany do Google Sheets.")
        st.rerun()
    except Exception as e:
        st.error(f"Nie udało się zapisać danych: {e}")


# =========================
# PEŁNA ROZPISKA
# =========================
st.subheader("Pełna rozpiska ćwiczeń")

st.markdown("""
<div class="section-note">
<b>Ważne:</b> to nie jest lista „wszystko codziennie”.<br>
To jest baza ćwiczeń podzielona na fazy. Aplikacja wyżej pokazuje Ci, co jest najważniejsze teraz.
</div>
""", unsafe_allow_html=True)

for ex in EXERCISES:
    with st.container():
        st.markdown(f"""
        <div class="exercise-card">
            <div class="exercise-title">{ex["name"]}</div>
            <div>
                <span class="badge">{ex["phase"]}</span>
                <span class="badge">{ex["category"]}</span>
            </div>
            <p><b>Dawka:</b> {ex["sets"]}</p>
            <p><b>Po co:</b> {ex["purpose"]}</p>
            <p><b>Jak wykonać:</b> {ex["how_to"]}</p>
            <p class="small-muted"><b>Komentarz:</b> {ex["comment"]}</p>
        </div>
        """, unsafe_allow_html=True)

        st.link_button("▶ Zobacz wykonanie", ex["video"], use_container_width=False)


# =========================
# DANE I PODGLĄD
# =========================
st.subheader("Twoje wpisy")

if df.empty:
    st.warning("Na razie nie ma jeszcze żadnych zapisanych danych.")
else:
    show_df = df.copy()
    show_df = show_df.sort_values(by="date", ascending=False)
    st.dataframe(show_df, use_container_width=True)

    recent_df = show_df.head(7)

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Ostatnie 7 wpisów**")
        st.dataframe(recent_df, use_container_width=True)

    with c2:
        if pain_avg is not None:
            st.write("**Podsumowanie**")
            st.markdown(f"""
            <div class="card">
                <p><b>Średni ból:</b> {pain_avg}/10</p>
                <p><b>Dni z ćwiczeniami:</b> {completed_entries}</p>
                <p><b>Wniosek:</b> regularność jest ważniejsza niż robienie ogromnej ilości ćwiczeń naraz.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write("**Podsumowanie**")
            st.markdown("""
            <div class="card">
                <p>Dodaj kilka wpisów, a tutaj pojawi się prosty obraz Twojego progresu.</p>
            </div>
            """, unsafe_allow_html=True)


# =========================
# STOPKA / KOMENTARZ
# =========================
st.markdown("""
<div class="section-note">
<b>Najważniejsza zasada:</b><br>
Nie musisz robić tych ćwiczeń non stop ani w dowolnej ilości. Najlepszy efekt da spokojny plan:
<b>3–4 sesje tygodniowo</b>, dobra technika, obserwacja bólu i stopniowe przechodzenie do kolejnej fazy.
</div>
""", unsafe_allow_html=True)
