import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from store import MemoryStore
from pomodoro_service import PomodoroService


class TestCompletePomodoro:
    def setup_method(self):
        self.store = MemoryStore()
        self.service = PomodoroService(self.store)

    def test_complete_returns_stats(self):
        stats = self.service.complete_pomodoro(25)
        assert stats["completed_count"] == 1
        assert stats["total_minutes"] == 25

    def test_complete_multiple_accumulates(self):
        self.service.complete_pomodoro(25)
        self.service.complete_pomodoro(25)
        stats = self.service.complete_pomodoro(25)
        assert stats["completed_count"] == 3
        assert stats["total_minutes"] == 75

    def test_complete_records_to_store(self):
        self.service.complete_pomodoro(25)
        records = self.store.get_today_records()
        assert len(records) == 1
        assert records[0]["duration_minutes"] == 25


class TestGetTodayStats:
    def setup_method(self):
        self.store = MemoryStore()
        self.service = PomodoroService(self.store)

    def test_empty_stats(self):
        stats = self.service.get_today_stats()
        assert stats["completed_count"] == 0
        assert stats["total_minutes"] == 0

    def test_stats_after_completions(self):
        self.service.complete_pomodoro(25)
        self.service.complete_pomodoro(25)
        stats = self.service.get_today_stats()
        assert stats["completed_count"] == 2
        assert stats["total_minutes"] == 50

    def test_different_durations(self):
        self.service.complete_pomodoro(25)
        self.service.complete_pomodoro(15)
        stats = self.service.get_today_stats()
        assert stats["completed_count"] == 2
        assert stats["total_minutes"] == 40
