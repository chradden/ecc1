
# 📄 Awork-Import Vorlage Generator

Dieses Projekt liest Auftragsbestätigungen im PDF-Format aus, extrahiert die Positionsdaten (inklusive Bullet Points) und schreibt sie in eine vorbereitete Awork-Importvorlage im Excel-Format.

---

## 📦 Voraussetzungen

Bevor du startest, stelle sicher, dass du folgende Tools installiert hast:

### 🛠️ Systemvoraussetzungen

* Python 3.10 oder höher
* `pip` Paketmanager
* **Tesseract OCR** (für Bild-PDFs → nicht zwingend, aber empfohlen):

  ```bash
  sudo apt-get install tesseract-ocr
  ```
* **Poppler Utils** (für PDF-Handling mit pdf2image → nur bei OCR-Version nötig):

  ```bash
  sudo apt-get install poppler-utils
  ```

### 📚 Python Abhängigkeiten

Installiere die benötigten Pakete über `pip`:

```bash
pip install -r requirements.txt
```

**Falls `requirements.txt` noch nicht existiert, hier sind die wichtigsten Pakete:**

```bash
pip install streamlit pandas python-dotenv openai PyMuPDF
```

**Optional (für OCR-Variante):**

```bash
pip install pytesseract pdf2image Pillow
```

---

## 🔑 Umgebungsvariablen

Das Projekt benötigt einen **OpenAI API Key**.

Erstelle eine `.env` Datei im Hauptverzeichnis:

```bash
OPENAI_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

---

## 🚀 Anwendung starten

```bash
streamlit run app.py
```

---

## 📝 Features

* 📄 Extrahiert Auftragspositionen inkl. Bullet-Point-Beschreibungen aus PDFs
* 🧠 Nutzt GPT-4o von OpenAI für intelligente Texterkennung
* 📊 Erstellt eine Excel-Importdatei kompatibel mit Awork
* 🛡️ Vertrauliche `.env` und `.venv` Dateien werden ignoriert

---

## 🔥 Nützliche Tipps

### Typische `.gitignore` für dieses Projekt:

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Environment
.venv/
env/
venv/
ENV/

# dotenv environment variables file
.env

# Mac OS
.DS_Store

# Jupyter Notebook checkpoints
.ipynb_checkpoints

# VS Code
.vscode/
```

---

## 🛡️ Sicherheitshinweise

* Niemals deinen `.env`-Datei mit API-Schlüsseln ins Repository pushen.
* Nutze `.gitignore`, um `.env` und `.venv` auszuschließen.
* Wenn versehentlich doch passiert: API-Key **sofort revoken** und Historie bereinigen (`git filter-repo`).

---

## 📚 Lizenz

MIT License.

---

