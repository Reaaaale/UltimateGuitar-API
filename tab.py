from typing import Any, Dict, List
import re

class UltimateTabInfo:
    """
    Represents the info of an Ultimate Guitar tab. Does not contain lyrics or chords.
    """
    def __init__(self, title: str, artist: str, author: str,
                 difficulty: str = None, key: str = None,
                 capo: str = None, tuning: str = None):
        self.title = title
        self.artist = artist
        self.author = author
        self.difficulty = difficulty
        self.key = key
        self.capo = capo
        self.tuning = tuning


class UltimateTab:
    """
    Represents an Ultimate Guitar tab containing lyrics and chords.
    Queue-like object that appends lines and can be parsed to JSON.
    """
    JSON_CONTAINER_NAME  = 'lines'
    JSON_KEY_CHORD_ARRAY = 'chords'
    JSON_KEY_NOTE        = 'note'
    JSON_KEY_LYRIC       = 'lyric'
    JSON_KEY_BLANK       = 'blank'
    JSON_KEY_TYPE        = 'type'
    JSON_KEY_LEAD_SPACES = 'pre_spaces'

    def __init__(self):
        self.lines: List[Dict[str, Any]] = []

    def _append_new_line(self, type: str, content_tag: str, content: Any) -> None:
        line: Dict[str, Any] = {'type': type}
        if content_tag is not None:
            line[content_tag] = content
        self.lines.append(line)

    def append_chord_line(self, chords_line: str) -> None:
        """
        Appends a chord line to the tab.
        """
        chords: List[Dict[str, Any]] = []
        leading_spaces = 0
        tokens = re.split(r'(\s+)', chords_line)  # mantiene spazi come token
        for token in tokens:
            if token.isspace():
                leading_spaces += len(token)
            elif token:
                chord = {
                    self.JSON_KEY_NOTE: token,
                    self.JSON_KEY_LEAD_SPACES: leading_spaces
                }
                chords.append(chord)
                leading_spaces = 0  # reset per il prossimo chord

        self._append_new_line(self.JSON_KEY_CHORD_ARRAY, self.JSON_KEY_CHORD_ARRAY, chords)

    def append_lyric_line(self, lyric_line: str) -> None:
        """
        Appends a lyric line to the tab.
        """
        self._append_new_line(self.JSON_KEY_LYRIC, self.JSON_KEY_LYRIC, lyric_line)

    def append_blank_line(self) -> None:
        """
        Appends a blank line to the tab.
        """
        self._append_new_line(self.JSON_KEY_BLANK, None, None)

    def as_json_dictionary(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation of the tab object.
        """
        return {self.JSON_CONTAINER_NAME: self.lines}
