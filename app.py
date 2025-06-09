import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
from openai import OpenAI
import io
import os
from dotenv import load_dotenv

# 🔑 API-Keys laden
load_dotenv()

# OpenAI Client initialisieren
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("📄 Auftragsbestätigung - Extraktion mit OpenAI (Bullet Points) und Awork-Import")

uploaded_pdf = st.file_uploader("Lade die Auftragsbestätigung hoch (PDF)", type="pdf")

AWORK_TEMPLATE_PATH = "awork_Importvorlage.xlsx"

def extract_text_pymupdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_positions_with_llm(text):
    st.text_area("📄 Extrahierter Text (PyMuPDF)", text, height=400)

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

    raw_output = response.choices[0].message.content

    # 🧹 Cleanup: Entferne ```json ... ``` falls vorhanden
    cleaned_output = raw_output.strip()
    if cleaned_output.startswith("```json"):
        cleaned_output = cleaned_output[7:]
    if cleaned_output.endswith("```"):
        cleaned_output = cleaned_output[:-3]

    try:
        positions_df = pd.read_json(io.StringIO(cleaned_output))
    except Exception as e:
        st.error(f"❌ Fehler beim Parsen der LLM-Antwort: {str(e)}")
        st.text_area("🪵 Rohantwort von GPT", raw_output, height=300)
        positions_df = pd.DataFrame()

    return positions_df


def fill_awork_template(positions_df):
    try:
        template = pd.read_excel(AWORK_TEMPLATE_PATH)

        st.write("📚 Vorlagen-Spalten:", template.columns.tolist())

        titel_spalte = None
        beschreibung_spalte = None
        stunden_spalte = None

        for col in template.columns:
            if col.strip().lower() in ["aufgabenname", "titel", "task name"]:
                titel_spalte = col
            if col.strip().lower() in ["beschreibung", "description"]:
                beschreibung_spalte = col
            if col.strip().lower() in ["geplanter aufwand", "geplante stunden", "planned effort"]:
                stunden_spalte = col

        if not titel_spalte or not beschreibung_spalte or not stunden_spalte:
            st.error("❌ Fehler: Die Awork-Vorlage hat keine passenden Spalten für Aufgabenname, Beschreibung und Geplanter Aufwand!")
            st.stop()

        # 📝 Neue Zeilen erzeugen
        new_data = {
            titel_spalte: positions_df['Titel'],            # Nur der Titel
            beschreibung_spalte: positions_df['Beschreibung'],  # Nur die Bullet Points
            stunden_spalte: positions_df['Menge'].str.extract(r"(\\d+)").astype(float).squeeze()  # "8 Tage" → 8
        }

        new_df = pd.DataFrame(new_data)

        updated_template = pd.concat([template, new_df], ignore_index=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            updated_template.to_excel(writer, index=False)
        output.seek(0)
        return output

    except Exception as e:
        st.error(f"❌ Fehler beim Ausfüllen der Vorlage: {str(e)}")
        return None



if uploaded_pdf:
    st.success("PDF erfolgreich hochgeladen! 📚")

    with st.spinner('🔍 Lese PDF mit PyMuPDF...'):
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
