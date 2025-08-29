# tab_parser.py
from typing import Dict, Any
from urllib.parse import urlparse, urlunparse
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

import cloudscraper
from bs4 import BeautifulSoup

from ug_parser import html_tab_to_json_dict
 # la tua funzione aggiornata (__NEXT_DATA__ + fallback <pre>)

# Headers "da browser"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

UG_PRE_CLASSES = ['js-tab-content', 'js-copy-content', 'js-store']  # solo hint legacy

_scraper = cloudscraper.create_scraper()  # <-- al posto di requests
RENDER_WAIT_SELECTORS = [
    "pre span[data-name]",  # chord spans dentro il pre
    "script#__NEXT_DATA__", # json next.js (se c'è)
]

def _get_html_via_playwright(url: str, timeout_ms: int = 12000) -> str:
    """Rende la pagina via browser headless e restituisce l'HTML renderizzato."""
    print(f"[pw] launch for {url}", flush=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=BROWSER_HEADERS["User-Agent"],
            locale="it-IT",
        )
        page = context.new_page()
        page.set_default_timeout(timeout_ms)
        page.set_extra_http_headers({
            "Accept": BROWSER_HEADERS["Accept"],
            "Accept-Language": BROWSER_HEADERS["Accept-Language"],
        })
        try:
            page.goto(url, wait_until="domcontentloaded")
            # aspetta uno dei selettori noti oppure networkidle come fallback
            found = False
            for sel in RENDER_WAIT_SELECTORS:
                try:
                    page.wait_for_selector(sel, state="attached", timeout=timeout_ms)
                    print(f"[pw] found selector: {sel}", flush=True)
                    found = True
                    break
                except PWTimeout:
                    continue
            if not found:
                # prova a lasciar finire le richieste
                try:
                    page.wait_for_load_state("networkidle", timeout=4000)
                    print("[pw] networkidle reached", flush=True)
                except PWTimeout:
                    pass
            html = page.content()
            print(f"[pw] got rendered html len={len(html)}", flush=True)
            return html
        finally:
            context.close()
            browser.close()

def _normalize_to_www(original_url: str) -> str:
    """Converte it./tabs. -> www.ultimate-guitar.com mantenendo path e query."""
    pu = urlparse(original_url)
    if pu.netloc in (
        "it.ultimate-guitar.com", "www.it.ultimate-guitar.com",
        "tabs.ultimate-guitar.com", "www.tabs.ultimate-guitar.com",
    ):
        pu = pu._replace(netloc="www.ultimate-guitar.com")
        return urlunparse(pu)
    return original_url

def _get_html(url: str) -> str:
    resp = _scraper.get(url, headers=BROWSER_HEADERS, timeout=25)
    # LOG MINIMI
    print(f"[fetch] status={resp.status_code} url={resp.url} len={len(resp.text)}")
    resp.raise_for_status()
    return resp.text

def _quick_dom_log(html: str) -> None:
    """Log di supporto: quanti <pre>, quanti span[data-name] nel migliore <pre>, __NEXT_DATA__ presente."""
    soup = BeautifulSoup(html, "html.parser")
    pres = soup.find_all("pre")
    best_pre = None
    best_score = -1
    for pre in pres:
        score = len(pre.select('span[data-name]'))
        if score > best_score:
            best_score = score
            best_pre = pre
    has_next = ('<script id="__NEXT_DATA__"' in html)
    print(f"[dom] pres={len(pres)} best_pre_spans={best_score} has_NEXT_DATA={has_next}")

def dict_from_ultimate_tab(url: str) -> Dict[str, Any]:
    print(f"[tab_parser] START url={url}", flush=True)

    def _try_one(u: str, use_browser: bool = False) -> Dict[str, Any] | None:
        try:
            html = _get_html_via_playwright(u) if use_browser else _get_html(u)
            _quick_dom_log(html)
            data = html_tab_to_json_dict(html, UG_PRE_CLASSES)
            if data and data.get("tab", {}).get("lines"):
                print(f"[parse] OK from {u}{' [pw]' if use_browser else ''}", flush=True)
                return data
        except Exception as e:
            print(f"[try_one] {u}{' [pw]' if use_browser else ''} -> ERROR: {e}", flush=True)
        return None

    # Varianti HTTP “semplici”
    variants: list[tuple[str, bool]] = []
    variants.append((url, False))
    www_url = _normalize_to_www(url)
    if www_url != url:
        variants.append((www_url, False))
    # print view
    if "print=1" not in url:
        sep = "&" if "?" in url else "?"
        variants.append((f"{url}{sep}print=1", False))
    if www_url != url:
        if "print=1" not in www_url:
            sep = "&" if "?" in www_url else "?"
            variants.append((f"{www_url}{sep}print=1", False))

    # Tenta prima tutte le varianti HTTP classiche
    seen = set()
    for v, is_browser in variants:
        if v in seen: 
            continue
        seen.add(v)
        print(f"[tab_parser] TRY {v}", flush=True)
        data = _try_one(v, use_browser=False)
        if data:
            return data

    # Fallback finale: Playwright (render JS) sulle due principali
    browser_variants = [url, www_url] if www_url != url else [url]
    for v in browser_variants:
        print(f"[tab_parser] TRY-PW {v}", flush=True)
        data = _try_one(v, use_browser=True)
        if data:
            return data

    print("[tab_parser] FAIL parse after all variants", flush=True)
    raise RuntimeError("Could not parse tab from the page.")