import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import io
import os

# --- Passwortschutz ---
def check_password():
    """Password input and verification"""
    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Passwort aus Speicher löschen
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔒 Passwort eingeben", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.text_input("🔒 Passwort eingeben", type="password", on_change=password_entered, key="password")
        st.error("❌ Falsches Passwort!")
        st.stop()
    else:
        pass

# --- Check Passwort ---
check_password()

# --- OpenAI Setup ---
try:
    # Lokale Entwicklung: .env Datei laden
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
except ImportError:
    # Falls dotenv nicht verfügbar: kein Problem, weiter mit Streamlit Secrets
    api_key = None

# Cloud Deployment: Streamlit Secrets
if not api_key:
    api_key = st.secrets["openai"]["api_key"]

# OpenAI Client Initialisierung
from openai import OpenAI
client = OpenAI(api_key=api_key)

# --- Streamlit App UI ---
st.title("📄 Awork-Import Vorlage Generator (lokal + Cloud)")

uploaded_pdf = st.file_uploader("Lade eine Auftragsbestätigung (PDF) hoch", type="pdf")

AWORK_TEMPLATE_PATH = "awork_Importvorlage.xlsx"

# --- PDF Text Extraktion ---
def extract_text_pymupdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# --- OpenAI GPT Positions Extraktion ---
def extract_positions_with_llm(text):
    st.text_area("📄 Extrahierter Text (Vorschau)", text, height=400)

    system_prompt = """
    Du bist ein Extraktionsassistent für Auftragsbestätigungen. Extrahiere aus dem folgenden Text alle Auftragspositionen.

    Gib für jede Position folgende Felder zurück:
    - Positionsnummer (Pos)
    - Titel der Position (Titel) — ein kurzer Name der Maßnahme.
    - Beschreibung (Beschreibung) — inklusive aller Bullet-Points oder Aufzählungen in strukturierter Form.
    - Menge (Menge)
    - Einzelpreis in Euro (Einzelpreis)
    - Gesamtpreis in Euro (Gesamtpreis)

    Gib ausschließlich reines JSON als Ausgabe, ohne Erklärungen oder Text drumherum.
    Beispiel:
    [
      {
        "Pos": "01",
        "Titel": "Grundlagenermittlung",
        "Beschreibung": "- Beschreiben der Anlagen und Prozesse\\n- Erfassen der IST-Energiebilanz (2019-2022)",
        "Menge": "8",
        "Einzelpreis": "940.00",
        "Gesamtpreis": "7520.00"
      }
    ]
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0
    )

    raw_output = response.choices[0].message.content.strip()

    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]
    if raw_output.endswith("```"):
        raw_output = raw_output[:-3]

    try:
        positions_df = pd.read_json(io.StringIO(raw_output))
    except Exception as e:
        st.error(f"❌ Fehler beim Parsen der LLM-Antwort: {str(e)}")
        st.text_area("🪵 Rohantwort von GPT", raw_output, height=300)
        positions_df = pd.DataFrame()

    return positions_df

# --- Awork Importvorlage füllen ---
# --- Awork Importvorlage füllen ---
def fill_awork_template(positions_df):
    try:
        template = pd.read_excel(AWORK_TEMPLATE_PATH)

        st.write("📚 Vorlagen-Spalten:", template.columns.tolist())

        # Spalten ermitteln
        titel_spalte = None
        beschreibung_spalte = None
        stunden_spalte = None
        for col in template.columns:
            c = col.strip().lower()
            if c in ["aufgabenname", "titel", "task name"]:
                titel_spalte = col
            if c in ["beschreibung", "description"]:
                beschreibung_spalte = col
            if c in ["geplanter aufwand", "geplante stunden", "planned effort"]:
                stunden_spalte = col

        if not titel_spalte or not beschreibung_spalte or not stunden_spalte:
            st.error("❌ Fehler: Die Awork-Vorlage hat keine passenden Spalten!")
            st.stop()

        # --- Hier kommt die Änderung: Menge als String
        menge_str = positions_df['Menge'].fillna("").astype(str)

        # Extrahiere die Zahl aus "8 Tage", "10" oder auch schon reinen Zahlen
        menge_zahl = (
            menge_str
            .str.extract(r"(\d+)", expand=False)    # String → erste Zahl
            .fillna("0")                            # fehlende → "0"
            .astype(float)                          # float
        )

        new_data = {
            titel_spalte:           positions_df['Titel'],
            beschreibung_spalte:    positions_df['Beschreibung'],
            stunden_spalte:         menge_zahl
        }

        new_df = pd.DataFrame(new_data)
        updated_template = pd.concat([template, new_df], ignore_index=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            updated_template.to_excel(writer, index=False)
        output.seek(0)
        return output

    except Exception as e:
        st.error(f"❌ Fehler beim Ausfüllen der Vorlage: {e}")
        return None


# --- Hauptlogik ---
if uploaded_pdf:
    st.success("✅ PDF erfolgreich hochgeladen!")

    with st.spinner('🔍 Extrahiere Text aus PDF...'):
        text = extract_text_pymupdf(uploaded_pdf)
        positions_df = extract_positions_with_llm(text)

        if positions_df.empty:
            st.error("❌ Keine Positionen gefunden! Bitte überprüfe den extrahierten Text.")
        else:
            st.dataframe(positions_df)

            with st.spinner('📝 Fülle awork Importvorlage...'):
                filled_excel = fill_awork_template(positions_df)

            if filled_excel:
                st.download_button(
                    label="📥 Fertige Awork-Importdatei herunterladen",
                    data=filled_excel,
                    file_name="awork_import_fertig.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
