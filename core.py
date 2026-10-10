import re

PITCH_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
LETTERS = ("C", "D", "E", "F", "G", "A", "B")
NATURAL_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
TUNING_MIDI = {6: 40, 5: 45, 4: 50, 3: 55, 2: 59, 1: 64}

CHORD_FORMULAS = {
    "": ((0, 1), (4, 3), (7, 5)),
    "m": ((0, 1), (3, 3), (7, 5)),
    "dim": ((0, 1), (3, 3), (6, 5)),
    "aug": ((0, 1), (4, 3), (8, 5)),
    "sus2": ((0, 1), (2, 2), (7, 5)),
    "sus4": ((0, 1), (5, 4), (7, 5)),
    "7": ((0, 1), (4, 3), (7, 5), (10, 7)),
    "maj7": ((0, 1), (4, 3), (7, 5), (11, 7)),
    "m7": ((0, 1), (3, 3), (7, 5), (10, 7)),
    "6": ((0, 1), (4, 3), (7, 5), (9, 6)),
    "m6": ((0, 1), (3, 3), (7, 5), (9, 6)),
    "m7b5": ((0, 1), (3, 3), (6, 5), (10, 7)),
    "dim7": ((0, 1), (3, 3), (6, 5), (9, 7)),
    "add9": ((0, 1), (4, 3), (7, 5), (2, 9)),
    "madd9": ((0, 1), (3, 3), (7, 5), (2, 9)),
    "9": ((0, 1), (4, 3), (7, 5), (10, 7), (2, 9)),
    "maj9": ((0, 1), (4, 3), (7, 5), (11, 7), (2, 9)),
    "m9": ((0, 1), (3, 3), (7, 5), (10, 7), (2, 9)),
    "11": ((0, 1), (4, 3), (7, 5), (10, 7), (2, 9), (5, 11)),
    "m11": ((0, 1), (3, 3), (7, 5), (10, 7), (2, 9), (5, 11)),
    "13": ((0, 1), (4, 3), (7, 5), (10, 7), (2, 9), (5, 11), (9, 13)),
}

# Degree distinguishes enharmonic intervals such as major sixth / diminished seventh.
INTERVAL_NAMES = {
    (0, 1): "根音", (2, 2): "大二度", (3, 3): "小三度",
    (4, 3): "大三度", (5, 4): "纯四度", (6, 5): "减五度",
    (7, 5): "纯五度", (8, 5): "增五度", (9, 6): "大六度",
    (2, 9): "大九度", (5, 11): "纯十一度", (9, 13): "大十三度",
    (9, 7): "减七度", (10, 7): "小七度", (11, 7): "大七度",
}


def toggle_position(selected: dict[int, int], string: int, fret: int) -> dict[int, int]:
    """Return a new shape: clicking an active position mutes that string."""
    note_at(string, fret)
    updated = dict(selected)
    if updated.get(string) == fret:
        del updated[string]
    else:
        updated[string] = fret
    return updated


KNOWN_SHAPES = {
    "C": (None, 3, 2, 0, 1, 0),
    "G": (3, 2, 0, 0, 0, 3),
    "D": (None, None, 0, 2, 3, 2),
    "A": (None, 0, 2, 2, 2, 0),
    "E": (0, 2, 2, 1, 0, 0),
    "Am": (None, 0, 2, 2, 1, 0),
    "Em": (0, 2, 2, 0, 0, 0),
    "Dm": (None, None, 0, 2, 3, 1),
    "F": (1, 3, 3, 2, 1, 1),
}

def _clean(text: str) -> str:
    return text.strip().replace("♯", "#").replace("♭", "b")

def note_to_pc(name: str) -> int:
    match = re.fullmatch(r"([A-Ga-g])((?:#+|b+)?)", _clean(name))
    if not match:
        raise ValueError("音名格式错误，例如 C、F#、Bb。")
    letter, accidental = match.groups()
    shift = accidental.count("#") - accidental.count("b")
    return (NATURAL_PC[letter.upper()] + shift) % 12

def _spell_note(root: str, semitones:int, degree:int) -> str:
    letter_index = (LETTERS.index(root[0]) + degree - 1) % 7
    letter = LETTERS[letter_index]
    target = (note_to_pc(root) + semitones) % 12
    delta = (target - NATURAL_PC[letter] + 6) % 12 - 6
    accidental = "#" * delta if delta >= 0 else "b" * (-delta)
    return letter + accidental

def chord_info(symbol: str) -> dict:
    match = re.fullmatch(r"([A-Ga-g])((?:#+|b+)?)(.*)", _clean(symbol))
    if not match:
        raise ValueError("和弦格式错误，例如 C、Am、G7、Bbmaj7。")
    letter, accidental, quality = match.groups()
    root = letter.upper() + accidental
    quality = {"maj": "", "min": "m"}.get(quality, quality)
    if quality not in CHORD_FORMULAS:
        raise ValueError("尚不支持该类型。支持：大/小三和弦、dim、aug、sus2、sus4、7、maj7、m7、6、m6、m7b5、dim7、add9、madd9、9、maj9、m9、11、m11、13。")
    root_pc = note_to_pc(root)
    formula = CHORD_FORMULAS[quality]
    return {
        "symbol": root + quality,
        "root_pc": root_pc,
        "intervals": [interval for interval, _ in formula],
        "interval_names": [INTERVAL_NAMES[(interval, degree)] for interval, degree in formula],
        "pitch_classes": [(root_pc + interval) % 12 for interval, _ in formula],
        "notes": [_spell_note(root, interval, degree) for interval, degree in formula],
    }

def chord_in_key(symbol: str, tonic: str = "C", mode: str = "大调") -> dict:
    """Label chord roots relative to a spelled major or natural-minor scale."""
    scales = {"大调": (0, 2, 4, 5, 7, 9, 11), "自然小调": (0, 2, 3, 5, 7, 8, 10)}
    if mode not in scales:
        raise ValueError("调式必须为大调或自然小调。")
    tonic = _clean(tonic)
    tonic_pc = note_to_pc(tonic)
    info = chord_info(symbol)
    match = re.fullmatch(r"([A-G])((?:#+|b+)?)(.*)", info["symbol"])
    letter, accidental, quality = match.groups()
    degree = (LETTERS.index(letter) - LETTERS.index(tonic[0].upper())) % 7
    expected = (tonic_pc + scales[mode][degree]) % 12
    delta = (info["root_pc"] - expected + 6) % 12 - 6
    prefix = "#" * delta if delta >= 0 else "b" * -delta
    scale_pcs = {(tonic_pc + interval) % 12 for interval in scales[mode]}
    outside = [name for name, pc in zip(info["notes"], info["pitch_classes"]) if pc not in scale_pcs]
    return {**info, "degree_symbol": f"{prefix}{degree + 1}{quality}",
            "diatonic": not outside, "outside_notes": outside}


def resolve_track_chord(value: str, tonic: str = "C", mode: str = "大调") -> dict:
    """Accept a chord symbol or a degree plus an explicit quality suffix."""
    value = _clean(value)
    match = re.fullmatch(r"([#b]*)([1-7])(.*)", value)
    if match:
        accidental, degree, quality = match.groups()
        scales = {"大调": (0, 2, 4, 5, 7, 9, 11), "自然小调": (0, 2, 3, 5, 7, 8, 10)}
        if mode not in scales:
            raise ValueError("调式必须为大调或自然小调。")
        tonic = _clean(tonic)
        note_to_pc(tonic)
        tonic = tonic[0].upper() + tonic[1:]
        degree = int(degree)
        semitones = scales[mode][degree - 1] + accidental.count("#") - accidental.count("b")
        value = _spell_note(tonic, semitones, degree) + quality
    return chord_in_key(value, tonic, mode)


def note_at(string: int, fret: int) -> int:
    if type(string) is not int or string not in TUNING_MIDI:
        raise ValueError("弦号必须是 1 到 6 的整数。")
    if type(fret) is not int or not 0 <= fret <= 24:
        raise ValueError("品位必须是 0 到 24 的整数。")
    return TUNING_MIDI[string] + fret


def fretboard_positions(symbol: str, max_fret: int = 12) -> list[dict]:
    if type(max_fret) is not int or not 0 <= max_fret <= 24:
        raise ValueError("最大品位必须是 0 到 24 的整数。")
    info = chord_info(symbol)
    names = dict(zip(info["pitch_classes"], info["notes"]))
    positions = []
    for string in TUNING_MIDI:
        for fret in range(max_fret + 1):
            midi = note_at(string, fret)
            if midi % 12 in names:
                positions.append({
                    "string": string, "fret": fret,
                    "midi": midi, "note": names[midi % 12],
                })
    return positions

def identify_chords(positions: list[tuple[int, int]], root: str | None = None,
                    allow_omissions: bool = False) -> list[dict]:
    """Match formulas, optionally omitting only root / perfect fifth.

    Keep all defining tones (thirds, sevenths, alterations and extensions).
    A minimum of two distinct played notes prevents single-note guesses.
    """
    roots = [root] if root is not None else PITCH_NAMES
    if root is not None:
        note_to_pc(root)
        root = _clean(root)
        roots = [root[0].upper() + root[1:]]
    if not positions:
        return []
    strings = [string for string, _ in positions]
    if len(strings) != len(set(strings)):
        raise ValueError("一组同时弹奏的按法里，每根弦只能选择一个品位。")
    midi_notes = [note_at(string, fret) for string, fret in positions]
    played = {midi % 12 for midi in midi_notes}
    bass_pc = min(midi_notes) % 12
    candidates = []
    for candidate_root in roots:
        for quality, formula in CHORD_FORMULAS.items():
            info = chord_info(candidate_root + quality)
            expected = set(info["pitch_classes"])
            missing = expected - played
            optional = {info["root_pc"], (info["root_pc"] + 7) % 12}
            if played != expected and not (
                allow_omissions and len(played) >= 2 and played < expected
                and missing <= optional
            ):
                continue
            names = dict(zip(info["pitch_classes"], info["notes"]))
            bass = names[bass_pc]
            name = info["symbol"]
            display_name = name if bass_pc == info["root_pc"] else f"{name}/{bass}"
            analysis = [
                {"note": note, "degree": degree, "interval": interval,
                 "semitones": distance, "present": pc in played}
                for note, (_, degree), interval, distance, pc in zip(
                    info["notes"], formula, info["interval_names"],
                    info["intervals"], info["pitch_classes"])
            ]
            candidates.append({**info, "bass": bass, "display_name": display_name,
                               "match_type": "omitted" if missing else "exact",
                               "missing_notes": [names[pc] for pc in info["pitch_classes"] if pc in missing],
                               "analysis": analysis})
    return sorted(candidates, key=lambda item: (
        item["match_type"] != "exact", len(item["missing_notes"]),
        item["bass"] != item["notes"][0], len(item["notes"])))


if __name__ == "__main__":
    print("C:", chord_info("C")["notes"])
    print("Am:", chord_info("Am")["notes"])
    print("C#:", chord_info("C#")["notes"])
    c_shape = [(5, 3), (4, 2), (3, 0), (2, 1), (1, 0)]
    print("C 常用按法:", [item["display_name"] for item in identify_chords(c_shape)])
    print("C 在 5 品以内的位置数:", len(fretboard_positions("C", 5)))
