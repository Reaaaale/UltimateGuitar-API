import requests
import json
import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from tab import UltimateTab, UltimateTabInfo

#Tutte le classi che mi serve prendere da UG
class UltimateTabInfo:
    def __init__(self, title, artist, author, difficulty, key, capo, tuning):
        self.title = title
        self.artist = artist
        self.author = author
        self.difficulty = difficulty
        self.key = key
        self.capo = capo
        self.tuning = tuning

   
class UltimateTab:
    # Rappresenta la struttura di una tab con le sue linee
    # (accordi, testo o righe vuote).
    def __init__(self):
        self.lines = []
    # Rappresenta una riga vuota
    def append_blank_line(self):
        self.lines.append({"type": "blank", "text": ""})
    # Rappresenta una riga di accordi
    def append_chord_line(self, line: str):
        self.lines.append({"type": "chords", "text": line})
    # Rappresenta una riga di testo
    def append_lyric_line(self, line: str):
        self.lines.append({"type": "lyrics", "text": line})
    # Rappresenta una riga di testo
    def as_json_dictionary(self):
        return {"lines": self.lines}

# Estrae le informazioni di una tab da un oggetto BeautifulSoup
def _tab_info_from_soup(soup: BeautifulSoup) -> UltimateTabInfo:
    try:
        song_title = soup.find(attrs={'itemprop': 'name'}).text # Titolo della canzone
        song_title = re.compile(re.escape('chords'), re.IGNORECASE).sub('', song_title).strip() # Rimuovi "chords"
    except:
        song_title = "UNKNOWN"

    try: # Estrae il nome dell'artista
        artist_name = soup.find(attrs={'class': 't_autor'}).text.replace('\n', '')
        artist_name = re.compile(re.escape('by'), re.IGNORECASE).sub('', artist_name).strip()
    except:
        artist_name = "UNKNOWN"
    # Estrae il nome dell'autore
    author = "UNKNOWN"
    difficulty = None
    key = None
    capo = None
    tuning = None
    # Estrae le informazioni aggiuntive
    try:
        info_header_text = soup.find(attrs={'class': 't_dt'}).text.replace('\n', '')
        info_headers = [x.lower() for x in info_header_text.split(' ') if x] 
        info_header_values = soup.findAll(attrs={'class': 't_dtde'})

        for index, header in enumerate(info_headers):
            try:
                if header == 'author':
                    author = info_header_values[index].a.text
                elif header == 'difficulty':
                    difficulty = info_header_values[index].text.strip()
                elif header == 'key':
                    key = info_header_values[index].text.strip()
                elif header == 'capo':
                    capo = info_header_values[index].text.strip()
                elif header == 'tuning':
                    tuning = info_header_values[index].text.strip()
            except:
                continue
    except:
        pass

    return UltimateTabInfo(song_title, artist_name, author, difficulty, key, capo, tuning)


def _extract_from_next_data_json(data: Dict[str, Any]) -> Dict[str, Any]:       #per ora non la sto usando
    def build_tab(tab_view: Dict[str, Any], song_info: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tab": {
                "title":       song_info.get("name", "UNKNOWN"),
                "artist_name": song_info.get("artist_name", "UNKNOWN"),
                "author":      (tab_view.get("author") or {}).get("username", "UNKNOWN"),
                "difficulty":  (tab_view.get("meta") or {}).get("difficulty"),
                "key":         (tab_view.get("meta") or {}).get("tonality"),
                "capo":        (tab_view.get("meta") or {}).get("capo"),
                "tuning":      (tab_view.get("meta") or {}).get("tuning"),
                "lines":       (tab_view.get("content") or {}).get("lines", [])
            }
        }

    page_props = (data.get("props") or {}).get("pageProps") or {}
    data_block = page_props.get("data") or {}
    tab_view = data_block.get("tab_view") or {}
    song_info = data_block.get("song") or {}
    if tab_view and song_info:
        return build_tab(tab_view, song_info)

    initial_state = page_props.get("initialState") or {}
    entities = (initial_state.get("store") or {}).get("entities") or {}

    tab_views_dict = entities.get("tabViews") or {}
    songs_dict = entities.get("songs") or {}

    if tab_views_dict and songs_dict:
        try:
            tab_view = next(iter(tab_views_dict.values()))
            song_info = next(iter(songs_dict.values()))
            if tab_view and song_info:
                return build_tab(tab_view, song_info)
        except StopIteration:
            pass

    return {}


def html_tab_to_json_dict(html_body: str, pre_class_tags: List[str]) -> Dict[str, Any]:
    """
    Converte l'HTML di Ultimate Guitar in un dizionario della tab.
    1) Prova JSON in __NEXT_DATA__, per il momento questo non sono riuscito ad usarlo
    2) Fallback robusto: trova il <pre> con più <span data-name="..."> (accordi)
    """
    soup = BeautifulSoup(html_body, "html.parser")

    # 1) Prova JSON moderno in __NEXT_DATA__
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if script_tag and script_tag.string:
        try:
            data = json.loads(script_tag.string)

            # Prova percorso classico
            page_props = (data.get("props") or {}).get("pageProps") or {}
            data_block = page_props.get("data") or {}
            tab_view = data_block.get("tab_view") or {}
            song_info = data_block.get("song") or {}

            # Se vuoto, prova percorso con initialState
            if not tab_view:
                initial_state = page_props.get("initialState") or {}
                entities = (initial_state.get("store") or {}).get("entities") or {}
                tab_views_dict = entities.get("tabViews") or {}
                songs_dict = entities.get("songs") or {}
                if tab_views_dict and songs_dict:
                    tab_view = next(iter(tab_views_dict.values()), {})
                    song_info = next(iter(songs_dict.values()), {})

            if tab_view:
                tab_json = {
                    "title":       song_info.get("name", "UNKNOWN"),
                    "artist_name": song_info.get("artist_name", "UNKNOWN"),
                    "author":      (tab_view.get("author") or {}).get("username", "UNKNOWN"),
                    "difficulty":  (tab_view.get("meta") or {}).get("difficulty"),
                    "key":         (tab_view.get("meta") or {}).get("tonality"),
                    "capo":        (tab_view.get("meta") or {}).get("capo"),
                    "tuning":      (tab_view.get("meta") or {}).get("tuning"),
                    "lines":       (tab_view.get("content") or {}).get("lines", [])
                }
                if tab_json["lines"]:
                    return {"tab": tab_json}
        except Exception:
            pass  # vai al fallback <pre>

    # 2) Fallback robusto su <pre>
    # Trova tutti i <pre>, scegli quello con più <span data-name="...">
    pre_candidates = soup.find_all("pre")
    best_pre = None
    best_score = -1
    for pre in pre_candidates:
        score = len(pre.select('span[data-name]'))
        if score > best_score:
            best_score = score
            best_pre = pre
    # Se non abbiamo spans (score 0), prendiamo il primo <pre> se esiste
    if best_pre is None and pre_candidates:
        best_pre = pre_candidates[0]

    if not best_pre:
        return {}

    
    formatted_tab_string = ''.join(map(str, best_pre.contents))


    tab = UltimateTab()
    re_span_tag = re.compile(r'<span[^>]*>|<\/span[^>]*>')
    for raw_line in formatted_tab_string.split('\n'):
        line = raw_line.strip('\r')
        if not line:
            tab.append_blank_line()
            continue
        if '<span' in line:
            sanitized = re_span_tag.sub(' ', line)
            # normalizza spazi multipli
            sanitized = re.sub(r'\s{2,}', ' ', sanitized)
            tab.append_chord_line(sanitized)
        else:
            tab.append_lyric_line(line)

    
    try:
        song_title = soup.find(attrs={'itemprop': 'name'}).text.strip()
    except Exception:
        song_title = "UNKNOWN"
    try:
        artist_name = soup.select_one('[data-artist-name]').get_text(strip=True)
    except Exception:
        artist_name = "UNKNOWN"

    tab_json = {
        "title": song_title,
        "artist_name": artist_name,
        "author": "UNKNOWN",
        "lines": tab.as_json_dictionary()['lines']
    }
    return {"tab": tab_json}

def fetch_tab_from_url(url: str) -> Dict[str, Any]:
    resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        raise Exception(f"Errore HTTP {resp.status_code}")
    return html_tab_to_json_dict(resp.text, pre_class_tags=["js-tab-content", "js-store"]) 


if __name__ == "__main__":
    url = "https://tabs.ultimate-guitar.com/tab/red-hot-chili-peppers/strip-my-mind-chords-517273"  
    tab_data = fetch_tab_from_url(url)
    print(json.dumps(tab_data, indent=2))
