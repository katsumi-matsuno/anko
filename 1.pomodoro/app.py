from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name(".gamification_data.json")


@dataclass(frozen=True)
class Badge:
    id: str
    name: str
    description: str


BADGES = {
    "streak_3": Badge("streak_3", "3日連続", "3日以上連続でポモドーロを完了"),
    "week_10": Badge("week_10", "今週10回完了", "直近7日で10回以上完了"),
    "month_40": Badge("month_40", "今月40回完了", "直近30日で40回以上完了"),
}


class PomodoroGamification:
    XP_PER_POMODORO = 25
    XP_PER_LEVEL = 100
    DAILY_TARGET = 4
    MAX_FOCUS_MINUTES = 240

    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self.data_file = data_file
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.data_file.exists():
            return {"sessions": []}
        try:
            data = json.loads(self.data_file.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"sessions": []}
            sessions = data.get("sessions", [])
            if not isinstance(sessions, list):
                sessions = []
            return {"sessions": sessions}
        except (json.JSONDecodeError, OSError):
            return {"sessions": []}

    def _save(self) -> None:
        self.data_file.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def complete_pomodoro(self, focus_minutes: int = 25, completed_at: date | None = None) -> dict[str, Any]:
        if focus_minutes <= 0 or focus_minutes > self.MAX_FOCUS_MINUTES:
            raise ValueError(f"focus_minutes must be between 1 and {self.MAX_FOCUS_MINUTES}")

        completed = completed_at or date.today()
        self._data["sessions"].append(
            {
                "date": completed.isoformat(),
                "focus_minutes": focus_minutes,
                "xp": self.XP_PER_POMODORO,
            }
        )
        self._save()
        return self.get_state()

    def get_state(self) -> dict[str, Any]:
        today = date.today()
        sessions = self._normalized_sessions()
        total_xp = sum(session["xp"] for session in sessions)
        level = (total_xp // self.XP_PER_LEVEL) + 1

        weekly = self._period_stats(sessions, today, 7)
        monthly = self._period_stats(sessions, today, 30)
        streak = self._current_streak(sessions, today)

        earned_badges = []
        if streak >= 3:
            earned_badges.append(BADGES["streak_3"])
        if weekly["completed"] >= 10:
            earned_badges.append(BADGES["week_10"])
        if monthly["completed"] >= 40:
            earned_badges.append(BADGES["month_40"])

        return {
            "xp": total_xp,
            "level": level,
            "next_level_xp": level * self.XP_PER_LEVEL,
            "streak_days": streak,
            "badges": [badge.__dict__ for badge in earned_badges],
            "weekly_stats": weekly,
            "monthly_stats": monthly,
            "recent_sessions": [
                {
                    "date": session["date"].isoformat(),
                    "focus_minutes": session["focus_minutes"],
                    "xp": session["xp"],
                }
                for session in sessions[-10:][::-1]
            ],
        }

    def _normalized_sessions(self) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for session in self._data.get("sessions", []):
            try:
                session_date = datetime.strptime(str(session.get("date", "")), "%Y-%m-%d").date()
                focus_minutes = int(session.get("focus_minutes", 25))
                xp = int(session.get("xp", self.XP_PER_POMODORO))
                if focus_minutes <= 0 or xp < 0:
                    continue
                normalized.append(
                    {
                        "date": session_date,
                        "focus_minutes": focus_minutes,
                        "xp": xp,
                    }
                )
            except (TypeError, ValueError):
                continue
        normalized.sort(key=lambda s: s["date"])
        return normalized

    def _period_stats(self, sessions: list[dict[str, Any]], today: date, days: int) -> dict[str, Any]:
        start = today - timedelta(days=days - 1)
        target_sessions = self.DAILY_TARGET * days
        in_period = [session for session in sessions if session["date"] >= start]
        completed = len(in_period)
        total_focus = sum(session["focus_minutes"] for session in in_period)
        completion_rate = round((completed / target_sessions) * 100, 1) if target_sessions else 0.0
        avg_focus = round((total_focus / completed), 1) if completed else 0.0
        return {
            "completed": completed,
            "completion_rate": min(completion_rate, 100.0),
            "average_focus_minutes": avg_focus,
            "total_focus_minutes": total_focus,
        }

    def _current_streak(self, sessions: list[dict[str, Any]], today: date) -> int:
        if not sessions:
            return 0

        completed_dates = sorted({session["date"] for session in sessions})
        last_date = completed_dates[-1]
        if (today - last_date).days > 1:
            return 0

        streak = 1
        cursor = last_date
        date_set = set(completed_dates)
        while (cursor - timedelta(days=1)) in date_set:
            streak += 1
            cursor -= timedelta(days=1)
        return streak


HTML = """<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Pomodoro Gamification</title>
  <style>
    body { font-family: sans-serif; max-width: 860px; margin: 20px auto; padding: 0 16px; background: #f9fafb; color: #111827; }
    .grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }
    .card { background: #fff; border-radius: 10px; padding: 14px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
    h1 { margin: 0 0 14px; }
    h2 { margin: 0 0 8px; font-size: 1rem; }
    .primary { background:#2563eb; color:#fff; border:none; border-radius:8px; padding:10px 14px; cursor:pointer; }
    .badge { display:inline-block; background:#f59e0b; color:#1f2937; border-radius:999px; padding:4px 10px; margin:4px 6px 0 0; font-size:.85rem; }
    .sessions li { margin: 6px 0; }
    .muted { color: #6b7280; }
    label, select { font-size: .95rem; }
  </style>
</head>
<body>
  <h1>�� Pomodoro ゲーミフィケーション</h1>
  <div class=\"card\">
    <label for=\"focusMinutes\">集中時間（分）</label>
    <select id=\"focusMinutes\">
      <option value=\"15\">15</option>
      <option value=\"25\" selected>25</option>
      <option value=\"30\">30</option>
      <option value=\"45\">45</option>
    </select>
    <button id=\"completeBtn\" class=\"primary\">ポモドーロ完了（+25XP）</button>
    <p class=\"muted\">完了するたびにXPと統計が更新されます。</p>
  </div>

  <div class=\"grid\">
    <section class=\"card\"><h2>経験値</h2><div id=\"xp\">0 XP</div><div id=\"level\">Lv.1</div></section>
    <section class=\"card\"><h2>ストリーク</h2><div id=\"streak\">0日連続</div></section>
    <section class=\"card\"><h2>週間統計</h2><div id=\"weekly\"></div></section>
    <section class=\"card\"><h2>月間統計</h2><div id=\"monthly\"></div></section>
  </div>

  <section class=\"card\" style=\"margin-top:12px\">
    <h2>達成バッジ</h2>
    <div id=\"badges\" class=\"muted\">まだバッジがありません</div>
  </section>

  <section class=\"card\" style=\"margin-top:12px\">
    <h2>最近の完了履歴</h2>
    <ul id=\"sessions\" class=\"sessions muted\"></ul>
  </section>

  <script>
    async function fetchState() {
      const res = await fetch('/api/state');
      return res.json();
    }

    function renderStats(node, stats) {
      node.innerHTML = `完了: ${stats.completed}回<br>完了率: ${stats.completion_rate}%<br>平均集中: ${stats.average_focus_minutes}分`;
    }

    function render(state) {
      document.getElementById('xp').textContent = `${state.xp} XP / 次Lvまで ${Math.max(state.next_level_xp - state.xp, 0)} XP`;
      document.getElementById('level').textContent = `Lv.${state.level}`;
      document.getElementById('streak').textContent = `${state.streak_days}日連続`;
      renderStats(document.getElementById('weekly'), state.weekly_stats);
      renderStats(document.getElementById('monthly'), state.monthly_stats);

      const badges = document.getElementById('badges');
      if (!state.badges.length) {
        badges.className = 'muted';
        badges.textContent = 'まだバッジがありません';
      } else {
        badges.className = '';
        badges.innerHTML = state.badges.map(b => `<span class=\"badge\" title=\"${b.description}\">🏅 ${b.name}</span>`).join('');
      }

      const sessions = document.getElementById('sessions');
      sessions.innerHTML = state.recent_sessions.length
        ? state.recent_sessions.map(s => `<li>${s.date}: ${s.focus_minutes}分 (+${s.xp}XP)</li>`).join('')
        : '<li>まだ完了履歴がありません</li>';
    }

    async function refresh() {
      const state = await fetchState();
      render(state);
    }

    document.getElementById('completeBtn').addEventListener('click', async () => {
      const minutes = parseInt(document.getElementById('focusMinutes').value, 10);
      await fetch('/api/complete', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ focus_minutes: minutes }),
      });
      await refresh();
    });

    refresh();
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    engine = PomodoroGamification()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send_html(HTML)
            return
        if self.path == "/api/state":
            self._send_json(self.engine.get_state())
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/complete":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        payload = {}
        if body:
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                self.send_error(HTTPStatus.BAD_REQUEST, "invalid json")
                return

        try:
            focus_minutes = int(payload.get("focus_minutes", 25))
            completed_at_raw = payload.get("completed_at")
            completed_at = (
                datetime.strptime(completed_at_raw, "%Y-%m-%d").date()
                if completed_at_raw
                else None
            )
            state = self.engine.complete_pomodoro(
                focus_minutes=focus_minutes,
                completed_at=completed_at,
            )
        except (ValueError, TypeError):
            self.send_error(HTTPStatus.BAD_REQUEST, "invalid payload")
            return

        self._send_json(state)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        pass

    def _send_html(self, html: str) -> None:
        encoded = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def run(port: int = 8000) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Pomodoro app running: http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
