import unittest

from core import (KNOWN_SHAPES, TUNING_MIDI, chord_info,
                  fretboard_positions, identify_chords, note_at, toggle_position)


class TheoryTests(unittest.TestCase):
    def test_extended_and_root_filter(self):
        positions = [(5, 3), (4, 2), (3, 0), (2, 3)]
        result = identify_chords(positions, root="C")
        self.assertEqual([c["symbol"] for c in result], ["Cadd9"])
        self.assertEqual(result[0]["analysis"][-1]["degree"], 9)
        self.assertEqual(result[0]["analysis"][-1]["semitones"], 2)
        self.assertEqual(identify_chords(positions, root="F"), [])
        self.assertEqual(chord_info("C9")["notes"], ["C", "E", "G", "Bb", "D"])

    def test_omitted_root_and_fifth(self):
        positions = [(6, 0), (3, 3)]  # E, Bb
        self.assertEqual(identify_chords(positions, root="C"), [])
        result = identify_chords(positions, root="C", allow_omissions=True)
        self.assertEqual([c["symbol"] for c in result], ["C7"])
        self.assertEqual(result[0]["missing_notes"], ["C", "G"])
        self.assertEqual(result[0]["display_name"], "C7/E")
        self.assertEqual(result[0]["match_type"], "omitted")
        self.assertEqual(identify_chords([(6, 0)], allow_omissions=True), [])
        self.assertEqual(identify_chords([(5, 3), (3, 0)], root="C", allow_omissions=True), [])
        self.assertEqual(identify_chords(positions + [(2, 0)], root="C", allow_omissions=True), [])

    def test_root_resolves_ambiguity(self):
        positions = [(5, 3), (4, 2), (3, 0), (1, 5)]
        self.assertEqual(identify_chords(positions, root="C")[0]["symbol"], "C6")
        self.assertEqual(identify_chords(positions, root="A")[0]["display_name"], "Am7/C")

    def test_click_selection(self):
        original = {5: 3}
        self.assertEqual(toggle_position(original, 5, 5), {5: 5})
        self.assertEqual(toggle_position(original, 5, 3), {})
        self.assertEqual(original, {5: 3})
        self.assertEqual(toggle_position({}, 1, 0), {1: 0})

    def test_interval_spelling(self):
        self.assertEqual(chord_info("C")["interval_names"], ["根音", "大三度", "纯五度"])
        self.assertEqual(chord_info("Cdim7")["interval_names"][-1], "减七度")
        self.assertEqual(chord_info("C6")["interval_names"][-1], "大六度")

    def test_spelling(self):
        for symbol, expected in {
            "C": ["C", "E", "G"], "Am": ["A", "C", "E"],
            "C#": ["C#", "E#", "G#"], "Bbmaj7": ["Bb", "D", "F", "A"],
            "Cdim7": ["C", "Eb", "Gb", "Bbb"],
        }.items():
            with self.subTest(symbol=symbol):
                self.assertEqual(chord_info(symbol)["notes"], expected)

    def test_every_preset_contains_exact_chord(self):
        for symbol, shape in KNOWN_SHAPES.items():
            positions = [(s, f) for s, f in zip(TUNING_MIDI, shape) if f is not None]
            with self.subTest(symbol=symbol):
                self.assertIn(symbol, [c["display_name"] for c in identify_chords(positions)])

    def test_inversion_and_ambiguous_names(self):
        self.assertIn("C/E", [c["display_name"] for c in identify_chords([(6, 0), (5, 3), (3, 0)])])
        candidates = identify_chords([(5, 3), (4, 2), (3, 0), (1, 5)])
        self.assertTrue({"C6", "Am7/C"}.issubset({c["display_name"] for c in candidates}))

    def test_positions_include_all_and_only_chord_tones(self):
        actual = {(p["string"], p["fret"]) for p in fretboard_positions("C", 12)}
        expected = {(s, f) for s in range(1, 7) for f in range(13)
                    if note_at(s, f) % 12 in {0, 4, 7}}
        self.assertEqual(actual, expected)

    def test_invalid_and_incomplete_input(self):
        self.assertEqual(identify_chords([]), [])
        self.assertEqual(identify_chords([(5, 3)]), [])
        for positions in [[(1, 0), (1, 3)], [(7, 0)], [(1, -1)]]:
            with self.assertRaises(ValueError):
                identify_chords(positions)
        for symbol in ["", "H", "C/E", "Cunknown"]:
            with self.assertRaises(ValueError):
                chord_info(symbol)


if __name__ == "__main__":
    unittest.main()
