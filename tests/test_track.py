import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from core import chord_in_key, resolve_track_chord
from track import overview_figures


class TrackTests(unittest.TestCase):
    def test_degrees_and_spelling(self):
        for chord, key, expected in [
            ("Cmaj7", "C", "1maj7"), ("Am7", "C", "6m7"),
            ("D7", "G", "57"), ("Bb", "C", "b7"),
            ("F#dim", "C", "#4dim"), ("Dbmaj7", "Db", "1maj7"),
        ]:
            with self.subTest(chord=chord, key=key):
                self.assertEqual(chord_in_key(chord, key)["degree_symbol"], expected)
        self.assertEqual(chord_in_key("Am", "A", "自然小调")["degree_symbol"], "1m")
        self.assertEqual(chord_in_key("C", "A", "自然小调")["degree_symbol"], "3")
        self.assertEqual(chord_in_key("D7", "C")["outside_notes"], ["F#"])

    def test_overview_timing_and_rows(self):
        bars = [{"slots": [{"input": "Cmaj7", "beats": 1}, {"input": "Am7", "beats": 3}]}]
        bars += [{"slots": [{"input": "G7", "beats": 4}]} for _ in range(4)]
        figures = overview_figures(bars, "C", "大调", "4/4")
        self.assertEqual(len(figures), 2)
        nodes = figures[0].data[1]
        self.assertEqual(list(nodes.x), [0, 1, 4, 8, 12])
        self.assertEqual(list(nodes.y), [0, 9, 7, 7, 7])
        self.assertEqual(list(nodes.text), ["1maj7", "6m7", "57", "57", "57"])
        self.assertEqual(figures[0].layout.shapes[1].x1, 4)
        self.assertEqual(list(figures[1].data[1].x), [0])
        invalid = overview_figures([{"slots": [{"input": "C", "beats": 5}]}], "C", "大调", "4/4")
        self.assertEqual(len(invalid[0].data[1].x), 0)

    def test_numeric_input(self):
        for value, tonic, expected in [("1maj7", "C", "Cmaj7"), ("6m7", "C", "Am7"),
                                       ("57", "G", "D7"), ("b7", "C", "Bb"),
                                       ("#4dim", "C", "F#dim"), ("1maj7", "Db", "Dbmaj7"),
                                       ("#7", "C#", "B##")]:
            with self.subTest(value=value, tonic=tonic):
                result = resolve_track_chord(value, tonic)
                self.assertEqual(result["symbol"], expected)
                self.assertEqual(result["degree_symbol"], value)
        self.assertEqual(resolve_track_chord("1m", "A", "自然小调")["symbol"], "Am")
        for value in ["8", "0", "1nope", ""]:
            with self.assertRaises(ValueError):
                resolve_track_chord(value)

    def test_panel_and_persistence(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        app.toggle(key="show_chord_track").set_value(True).run()
        app.text_input(key="slot_input_0").set_value("1maj7").run()
        self.assertTrue(any("Cmaj7 ↔ 1maj7" in m.value for m in app.markdown))
        app.selectbox(key="edit_track_tonic").set_value("G").run()
        self.assertTrue(any("Gmaj7 ↔ 1maj7" in m.value for m in app.markdown))
        app.number_input(key="slot_beats_0").set_value(2).run()
        app.button(key="add_slot_0").click().run()
        app.text_input(key="slot_input_4").set_value("D7").run()
        self.assertTrue(any("D7 ↔ 57" in m.value for m in app.markdown))
        app.selectbox(key="edit_track_meter").set_value("3/4").run()
        self.assertTrue(app.error)
        app.number_input(key="slot_beats_4").set_value(1).run()
        app.toggle(key="show_chord_track").set_value(False).run()
        app.toggle(key="show_chord_track").set_value(True).run()
        self.assertEqual(app.text_input(key="slot_input_0").value, "1maj7")
        app.button(key="remove_slot_4").click().run()
        self.assertEqual(len(app.session_state.track_bars[0]["slots"]), 1)
        app.button(key="add_track_bar").click().run()
        self.assertEqual(len(app.session_state.track_bars), 5)
        app.button(key="remove_bar_5").click().run()
        self.assertEqual(len(app.session_state.track_bars), 4)
        app.radio[0].set_value("反向识别").run()
        self.assertEqual(app.text_input(key="slot_input_0").value, "1maj7")
        self.assertFalse(app.exception)
