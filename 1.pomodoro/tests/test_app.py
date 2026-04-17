import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


class TestIndex:
    def setup_method(self):
        app = create_app({"TESTING": True})
        self.client = app.test_client()

    def test_index_returns_200(self):
        resp = self.client.get("/")
        assert resp.status_code == 200


class TestCompleteAPI:
    def setup_method(self):
        app = create_app({"TESTING": True})
        self.client = app.test_client()

    def test_complete_returns_stats(self):
        resp = self.client.post(
            "/api/complete",
            json={"duration_minutes": 25},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["completed_count"] == 1
        assert data["total_minutes"] == 25

    def test_complete_default_duration(self):
        resp = self.client.post("/api/complete", json={})
        data = resp.get_json()
        assert data["completed_count"] == 1
        assert data["total_minutes"] == 25

    def test_complete_accumulates(self):
        self.client.post("/api/complete", json={"duration_minutes": 25})
        resp = self.client.post("/api/complete", json={"duration_minutes": 25})
        data = resp.get_json()
        assert data["completed_count"] == 2
        assert data["total_minutes"] == 50


class TestStatsAPI:
    def setup_method(self):
        app = create_app({"TESTING": True})
        self.client = app.test_client()

    def test_stats_empty(self):
        resp = self.client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["completed_count"] == 0
        assert data["total_minutes"] == 0

    def test_stats_after_complete(self):
        self.client.post("/api/complete", json={"duration_minutes": 25})
        resp = self.client.get("/api/stats")
        data = resp.get_json()
        assert data["completed_count"] == 1
        assert data["total_minutes"] == 25
