import sys
import os
from unittest.mock import patch
from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from store import MemoryStore


class TestMemoryStoreAddRecord:
    def test_add_single_record(self):
        store = MemoryStore()
        store.add_record(25)
        records = store.get_today_records()
        assert len(records) == 1
        assert records[0]["duration_minutes"] == 25

    def test_add_multiple_records(self):
        store = MemoryStore()
        store.add_record(25)
        store.add_record(25)
        store.add_record(15)
        records = store.get_today_records()
        assert len(records) == 3


class TestMemoryStoreGetTodayRecords:
    def test_empty_store_returns_empty_list(self):
        store = MemoryStore()
        assert store.get_today_records() == []

    def test_filters_by_today(self):
        store = MemoryStore()
        store.add_record(25)
        # 過去の日付のレコードを手動追加
        store._records.append({
            "date": "2000-01-01",
            "duration_minutes": 25,
        })
        records = store.get_today_records()
        assert len(records) == 1
        assert records[0]["date"] == date.today().isoformat()

    def test_record_contains_date_and_duration(self):
        store = MemoryStore()
        store.add_record(25)
        record = store.get_today_records()[0]
        assert "date" in record
        assert "duration_minutes" in record
        assert record["date"] == date.today().isoformat()
        assert record["duration_minutes"] == 25


class TestMemoryStoreClear:
    def test_clear_removes_all_records(self):
        store = MemoryStore()
        store.add_record(25)
        store.add_record(25)
        store.clear()
        assert store.get_today_records() == []

    def test_clear_on_empty_store(self):
        store = MemoryStore()
        store.clear()
        assert store.get_today_records() == []
