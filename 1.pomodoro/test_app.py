import importlib.util
import pathlib
import unittest

APP_PATH = pathlib.Path(__file__).with_name("app.py")
spec = importlib.util.spec_from_file_location("pomodoro_app", APP_PATH)
app = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(app)


class PomodoroAppTests(unittest.TestCase):
    def test_progress_offset_boundaries(self):
        circumference = 100.0
        self.assertEqual(app.progress_offset(10, 10, circumference), 0.0)
        self.assertEqual(app.progress_offset(10, 0, circumference), 100.0)
        self.assertEqual(app.progress_offset(10, -1, circumference), 100.0)

    def test_progress_color_gradient(self):
        self.assertEqual(app.progress_color(100, 100), (59, 130, 246))
        self.assertEqual(app.progress_color(100, 50), (234, 179, 8))
        self.assertEqual(app.progress_color(100, 0), (239, 68, 68))
        self.assertEqual(app.progress_color(100, -10), (239, 68, 68))
        self.assertEqual(app.progress_color(100, 999), (59, 130, 246))

    def test_build_html_includes_ui_elements(self):
        html = app.build_html("b")
        self.assertIn('id="progress"', html)
        self.assertIn('id="fx"', html)
        self.assertIn('A/Bテスト: variant=B', html)


if __name__ == "__main__":
    unittest.main()
