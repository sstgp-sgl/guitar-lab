import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_root_and_omission_controls(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        app.radio[0].set_value("反向识别").run()
        app.button(key="fret_6_0").click().run()
        app.button(key="fret_3_3").click().run()
        app.selectbox(key="analysis_root").set_value("C").run()
        self.assertFalse(app.subheader)
        app.checkbox(key="allow_omissions").check().run()
        self.assertEqual(app.subheader[0].value, "C7/E")
        self.assertTrue(any("省略了：C、G" in w.value for w in app.warning))
        self.assertEqual(len(app.table[0].value), 4)
        app.checkbox(key="allow_omissions").uncheck().run()
        self.assertFalse(app.subheader)
        self.assertFalse(app.exception)

    def test_modes_and_invalid_symbol(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
        self.assertFalse(app.exception)
        app.radio[0].set_value("常用按法").run()
        self.assertFalse(app.exception)
        app.radio[0].set_value("反向识别").run()
        self.assertFalse(app.exception)
        app.button(key="fret_5_3").click().run()
        app.button(key="fret_4_2").click().run()
        app.button(key="fret_3_0").click().run()
        self.assertEqual(app.subheader[0].value, "C")
        self.assertTrue(any("大三度" in m.value for m in app.markdown))
        app.button(key="fret_5_5").click().run()
        self.assertEqual(app.session_state.selected_positions[5], 5)
        app.button(key="fret_5_5").click().run()
        self.assertNotIn(5, app.session_state.selected_positions)
        app.button[0].click().run()
        self.assertEqual(app.session_state.selected_positions, {})
        self.assertTrue(app.info)
        app.button[1].click().run()
        self.assertEqual(app.subheader[0].value, "C")
        app.button[2].click().run()
        self.assertEqual(app.subheader[0].value, "Am")
        app.button(key="fret_1_12").click().run()
        app.slider[0].set_value(5).run()
        self.assertTrue(app.warning)
        self.assertEqual(app.session_state.selected_positions[1], 12)
        self.assertFalse(app.exception)
        app.radio[0].set_value("和弦音位置").run()
        app.text_input[0].set_value("H").run()
        self.assertTrue(app.error)
        self.assertFalse(app.exception)
