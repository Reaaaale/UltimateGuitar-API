# main.py
from fastapi import FastAPI, HTTPException, Query
from urllib.parse import urlparse
from tab_parser import dict_from_ultimate_tab  # importiamo la logica di parsing

app = FastAPI()

SUPPORTED_UG_URI = "tabs.ultimate-guitar.com"

@app.get("/")
def index():
    return {"message": "hi"}

@app.get("/tab")
def tab(url: str = Query(..., description="Ultimate Guitar tab URL")):
    try:
        parsed_url = urlparse(url)
        if parsed_url.netloc != SUPPORTED_UG_URI:
            raise HTTPException(status_code=400, detail="unsupported url scheme")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    tab_dict = dict_from_ultimate_tab(url)
    return tab_dict
