class PomodoroService:
    def __init__(self, store):
        self._store = store

    def complete_pomodoro(self, duration_minutes):
        self._store.add_record(duration_minutes)
        return self.get_today_stats()

    def get_today_stats(self):
        records = self._store.get_today_records()
        total_minutes = sum(r["duration_minutes"] for r in records)
        return {
            "completed_count": len(records),
            "total_minutes": total_minutes,
        }
