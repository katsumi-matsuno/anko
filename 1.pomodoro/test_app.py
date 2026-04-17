from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import PomodoroGamification


class PomodoroGamificationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data_file = Path(self.tmp_dir.name) / "state.json"
        self.engine = PomodoroGamification(data_file=self.data_file)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_xp_and_level_increase(self) -> None:
        for _ in range(5):
            self.engine.complete_pomodoro(focus_minutes=25)

        state = self.engine.get_state()
        self.assertEqual(state["xp"], 125)
        self.assertEqual(state["level"], 2)

    def test_streak_resets_when_day_is_missed(self) -> None:
        today = date.today()
        self.engine.complete_pomodoro(completed_at=today - timedelta(days=4))
        self.engine.complete_pomodoro(completed_at=today - timedelta(days=3))

        state = self.engine.get_state()
        self.assertEqual(state["streak_days"], 0)

    def test_weekly_badge_and_stats(self) -> None:
        today = date.today()
        for offset in range(7):
            for _ in range(2):
                self.engine.complete_pomodoro(completed_at=today - timedelta(days=offset), focus_minutes=25)

        state = self.engine.get_state()
        badge_ids = {badge["id"] for badge in state["badges"]}
        self.assertIn("week_10", badge_ids)
        self.assertEqual(state["weekly_stats"]["completed"], 14)
        self.assertEqual(state["weekly_stats"]["average_focus_minutes"], 25.0)


if __name__ == "__main__":
    unittest.main()
