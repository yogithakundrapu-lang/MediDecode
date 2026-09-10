# MediDecode — Medical Report Simplifier

MediDecode turns confusing medical lab reports into plain-language explanations, with
color-coded risk levels, food advice, and general guidance — so patients without a
medical background can understand their own reports.

## Tech Stack

* **Frontend:** HTML5, CSS3, vanilla JavaScript (+ Chart.js from CDN for graphs)
* **Backend:** Python Flask
* **Database:** MySQL
* **OCR:** Tesseract (via `pytesseract` + `pdf2image`)

## Project Structure

```
MediDecode/
├── index.html          Splash screen
├── language.html        Language selection (English / Telugu / Hindi)
├── login.html
├── signup.html
├── dashboard.html
├── upload.html          Upload / camera capture
├── reports.html         Simplified report explanation
├── history.html         Report history (search, sort, download, delete)
├── profile.html
├── notifications.html
├── health.html           Health Summary + Health Advice tabs
├── hospitals.html / medicalshops.html / labs.html   Nearby services
├── settings.html
├── feedback.html
├── support.html         FAQ, contact, about
├── css/style.css        Shared design system (single stylesheet, all pages)
├── js/
│   ├── app-shell.js      Renders sidebar + topbar on every page
│   ├── i18n.js            English/Telugu/Hindi translation dictionary
│   └── script.js          Splash-screen redirect logic
├── python/
│   ├── app.py             Flask backend (auth, upload/OCR, reports, etc.)
│   └── requirements.txt
├── database.sql          MySQL schema + seed reference ranges
└── README.md
```

## Backend Setup

1. **Install MySQL** and create the database:

```bash
   mysql -u root -p < database.sql
   ```

2. **Install Tesseract OCR** (system package, not pip):

   * Ubuntu/Debian: `sudo apt install tesseract-ocr poppler-utils`
   * macOS: `brew install tesseract poppler`
   * Windows: install from https://github.com/UB-Mannheim/tesseract/wiki and add to PATH
3. **Install Python dependencies:**

```bash
   cd python
   pip install -r requirements.txt
   ```

4. **Set environment variables** (or edit the defaults in `app.py`):

```bash
   export DB\\\_HOST=localhost
   export DB\\\_USER=root
   export DB\\\_PASSWORD=yourpassword
   export DB\\\_NAME=medidecode
   export MEDIDECODE\\\_SECRET=some-long-random-string
   ```

5. **Run the backend:**

```bash
   python app.py
   ```

The API will be available at `http://localhost:5000/api/...`

## Frontend

The frontend is static HTML/CSS/JS — no build step required. Every page falls back
gracefully to demo data if the backend isn't running yet, so the UI can be reviewed
and presented on its own.

Open `index.html` in a browser, or serve the folder with any static server, e.g.:

```bash
python -m http.server 8080
```

## Notes on the OCR / Simplification Engine

`app.py` uses a transparent, rule-based approach: Tesseract OCR extracts the raw text
from an uploaded PDF/image, then regex patterns match known medical parameters
(Hemoglobin, Blood Sugar, Cholesterol, Platelets, Vitamin D) against reference ranges
stored in `parameter\\\_reference`. This keeps every result explainable — there's no
black-box model deciding a patient's health status. The reference table can be
extended with more parameters as needed.

## Design System

All pages share one stylesheet (`css/style.css`) and one shared JS shell
(`js/app-shell.js`), so the sidebar, header, cards, buttons, and colors stay
pixel-consistent across every page — new pages will always match the original
dashboard design.

