from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def run() -> None:
    base_dir = Path(__file__).resolve().parent
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(base_dir), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler)
    print("Pomodoro UI server is running at http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    run()
