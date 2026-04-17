from datetime import date


class MemoryStore:
    def __init__(self):
        self._records = []

    def add_record(self, duration_minutes):
        self._records.append({
            "date": date.today().isoformat(),
            "duration_minutes": duration_minutes,
        })

    def get_today_records(self):
        today = date.today().isoformat()
        return [r for r in self._records if r["date"] == today]

    def clear(self):
        self._records.clear()
