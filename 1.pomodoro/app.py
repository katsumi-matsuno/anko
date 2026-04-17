from flask import Flask, render_template, request, jsonify
from store import MemoryStore
from pomodoro_service import PomodoroService


def create_app(config=None):
    app = Flask(__name__)

    if config:
        app.config.update(config)

    store = MemoryStore()
    service = PomodoroService(store)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/complete", methods=["POST"])
    def complete():
        data = request.get_json(silent=True) or {}
        duration = data.get("duration_minutes", 25)
        stats = service.complete_pomodoro(duration)
        return jsonify(stats)

    @app.route("/api/stats")
    def stats():
        return jsonify(service.get_today_stats())

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
