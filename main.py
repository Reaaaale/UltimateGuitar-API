# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from urllib.parse import urlparse
import io
from datetime import datetime


app = FastAPI(
    title="Ultimate Guitar Tabs API",
    description="API per ottenere accordi da Ultimate Guitar",
    version="1.0"
)

# Domini UG supportati (puliti)
SUPPORTED_UG_DOMAINS = [
    "www.ultimate-guitar.com",
    "ultimate-guitar.com",
    "tabs.ultimate-guitar.com",
    "www.tabs.ultimate-guitar.com",
    "it.ultimate-guitar.com",
    "www.it.ultimate-guitar.com",
]

@app.get("/")
def index():
    return {"message": "Ultimate Guitar Tabs API is running!"} 

@app.get("/tab")
def tab(url: str = Query(..., description="Ultimate Guitar tab URL")):
    print(f"[main] /tab called with url={url}", flush=True)

    parsed_url = urlparse(url)
    if parsed_url.netloc not in SUPPORTED_UG_DOMAINS:
        print(f"[main] domain rejected: {parsed_url.netloc}", flush=True)
        raise HTTPException(status_code=400, detail="Unsupported URL domain")

    try:
        # Lazy import: evita effetti collaterali all'import del modulo
        from tab_parser import dict_from_ultimate_tab

        tab_dict = dict_from_ultimate_tab(url)
        print("[main] dict_from_ultimate_tab returned", flush=True)

        if not tab_dict:
            raise HTTPException(status_code=404, detail="Tab not found or could not be parsed")
        return tab_dict
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[main] ERROR: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@app.get("/tab/pdf")
def tab_pdf(url: str = Query(..., description="Ultimate Guitar tab URL")):
    print(f"[main] /tab/pdf called with url={url}", flush=True)
    parsed_url = urlparse(url)
    if parsed_url.netloc not in SUPPORTED_UG_DOMAINS:
        raise HTTPException(status_code=400, detail="Unsupported URL domain")

    try:
        from tab_parser import dict_from_ultimate_tab
        data = dict_from_ultimate_tab(url)
        tab = data.get("tab", {})
        title = tab.get("title") or "UNKNOWN"
        artist = tab.get("artist_name") or "UNKNOWN"
        lines = tab.get("lines") or []

        # genera PDF 
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        width, height = A4

        # margini e font monospace
        left = 15 * mm
        right = 15 * mm
        top = 15 * mm
        bottom = 15 * mm
        usable_width = width - left - right

        # Titolo & meta
        c.setFont("Courier-Bold", 14)
        c.drawString(left, height - top, (title or "UNKNOWN"))
        c.setFont("Courier", 10)
        c.drawString(left, height - top - 14, f"Artist: {artist or 'UNKNOWN'}")
        c.drawString(left, height - top - 28, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # posizione iniziale testo
        y = height - top - 45
        line_height = 12  
        c.setFont("Courier", 10)

        def draw_line(text: str):
            nonlocal y
            
            max_chars = 110
            chunks = [text[i:i+max_chars] for i in range(0, len(text), max_chars)] or [""]
            for chunk in chunks:
                if y < bottom + line_height:
                    c.showPage()
                    c.setFont("Courier", 10)
                    y = height - top
                c.drawString(left, y, chunk)
                y -= line_height

        # stampa contenuto
        for row in lines:
            typ = row.get("type")
            
            text = row.get("text", "")
            if typ == "blank":
                draw_line("")  
            elif typ in ("lyrics", "chords"):
                draw_line(text)
            else:
                # fallback
                draw_line(text)

        c.showPage()
        c.save()
        buf.seek(0)

        
        safe_title = (title or "tab").replace("/", "-").replace("\\", "-")
        filename = f"{safe_title}.pdf"

        return StreamingResponse(
            buf,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
