# Ultimate Guitar Tabs → PDF API

Questa API consente di inserire un **link di Ultimate Guitar** e ricevere in risposta un file **PDF con gli accordi e il testo**.

---

## 📂 Struttura del progetto

```
.
├── main.py          # Entrypoint FastAPI con le route principali
├── views.py         # Versione minimale di API (legacy)
├── tab.py           # Classi per rappresentare info e linee di una tab
├── tab_parser.py    # Gestione fetch/render delle pagine UG e parsing
├── ug_parser.py     # Conversione HTML/JSON UG in dizionario tab
├── requirements.txt # Dipendenze Python
```

---

## 🚀 Installazione

### Requisiti
- Python **3.10+**
- pip
- Facoltativo: venv

### Setup
```bash
cd UltimateGuitarTabsAPI

python -m venv .venv
# Linux/Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ Avvio del server

```bash
uvicorn main:app --reload
```

Server disponibile su:

```
http://127.0.0.1:8000
```

---

## 📡 Endpoint API

### 1. Healthcheck
```
GET /
```
Risposta:
```json
{ "message": "Ultimate Guitar Tabs API is running!" }
```

### 2. Tab in JSON
```
GET /tab?url=<URL>
```
Esempio di risposta:
```json
{
  "tab": {
    "title": "Song Title",
    "artist_name": "Artist",
    "author": "UNKNOWN",
    "lines": [
      { "type": "lyrics", "text": "Some lyric line" },
      { "type": "chords", "text": "C   G   Am   F" },
      { "type": "blank", "text": "" }
    ]
  }
}
```

### 3. Tab in PDF
```
GET /tab/pdf?url=<URL>
```
Esempio:
```bash
curl -X GET "http://127.0.0.1:8000/tab/pdf?url=https://tabs.ultimate-guitar.com/tab/artist/song-chords-1234567" \
  --output song.pdf
```

---

## 🛠️ Funzionamento

- **tab_parser.py**: scarica la pagina UG con `cloudscraper` o `playwright`, normalizza URL, converte HTML in JSON.  
- **ug_parser.py**: parsing moderno (JSON `__NEXT_DATA__`) o fallback `<pre>`; genera righe `lyrics`, `chords`, `blank`.  
- **tab.py**: modelli per la tab (info e linee), conversione in JSON.  
- **main.py**: definisce API `/tab` e `/tab/pdf`, genera PDF con `reportlab`.  
- **views.py**: versione ridotta che espone solo `/tab`.

---

## 📦 Dipendenze principali

- fastapi + uvicorn → server API  
- cloudscraper → fetch HTML  
- playwright → rendering headless  
- beautifulsoup4 → parsing HTML  
- reportlab → generazione PDF  
- requests → fallback HTTP  

---

## ⚠️ Limitazioni

- Alcuni URL potrebbero non funzionare se UG cambia struttura.  
- Non fare troppe richieste in poco tempo per evitare blocchi da UG.  
- Rispetta i **termini di servizio di Ultimate Guitar** e il diritto d’autore.

---

## 📖 Esempio Python client

```python
import requests

URL = "http://127.0.0.1:8000/tab/pdf"
payload = {"url": "https://tabs.ultimate-guitar.com/tab/artist/song-chords-1234567"}

r = requests.get(URL, params=payload)
r.raise_for_status()

with open("song.pdf", "wb") as f:
    f.write(r.content)

print("PDF salvato come song.pdf")
```

---

## 📜 Licenza

Uso didattico/sperimentale. Rispettare copyright e termini UG.
