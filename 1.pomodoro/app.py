from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

FOCUS_SECONDS = 25 * 60
BREAK_SECONDS = 5 * 60


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def progress_offset(total_seconds: int, remaining_seconds: float, circumference: float) -> float:
    """円形プログレスの stroke-dashoffset を返す。"""
    if total_seconds <= 0:
        return circumference
    remaining_ratio = _clamp(remaining_seconds / total_seconds, 0.0, 1.0)
    return circumference * (1.0 - remaining_ratio)


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * _clamp(t, 0.0, 1.0))


def progress_color(total_seconds: int, remaining_seconds: float) -> tuple[int, int, int]:
    """残り時間に応じた色（青→黄→赤）を返す。"""
    if total_seconds <= 0:
        return (239, 68, 68)

    elapsed_ratio = 1.0 - _clamp(remaining_seconds / total_seconds, 0.0, 1.0)
    blue = (59, 130, 246)
    yellow = (234, 179, 8)
    red = (239, 68, 68)

    if elapsed_ratio < 0.5:
        t = elapsed_ratio / 0.5
        return tuple(_lerp(blue[i], yellow[i], t) for i in range(3))

    t = (elapsed_ratio - 0.5) / 0.5
    return tuple(_lerp(yellow[i], red[i], t) for i in range(3))


def build_html(variant: str = "a") -> str:
    variant = "b" if variant.lower() == "b" else "a"
    return f"""<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Pomodoro Timer</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg1: #0b1020;
      --bg2: #0f1b3d;
      --fg: #f4f7ff;
      --muted: #a8b2d1;
      --ring: rgb(59,130,246);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      color: var(--fg);
      background: radial-gradient(circle at 20% 20%, #162a59 0%, var(--bg1) 45%, #080b16 100%);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial;
      overflow: hidden;
    }}
    #fx {{ position: fixed; inset: 0; z-index: 0; opacity: 0.7; }}
    .card {{
      width: min(92vw, 420px);
      background: rgba(8, 12, 26, 0.58);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      backdrop-filter: blur(8px);
      padding: 20px;
      text-align: center;
      position: relative;
      z-index: 1;
      box-shadow: 0 20px 48px rgba(0,0,0,.4);
    }}
    .phase {{ color: var(--muted); margin-bottom: 8px; }}
    .timer-wrap {{ width: 320px; max-width: 80vw; margin: 0 auto; position: relative; }}
    svg {{ width: 100%; height: auto; transform: rotate(-90deg); }}
    .track {{ stroke: rgba(255,255,255,.1); fill: none; stroke-width: 14; }}
    .progress {{
      fill: none;
      stroke: var(--ring);
      stroke-linecap: round;
      stroke-width: 14;
      transition: stroke .2s linear;
      filter: drop-shadow(0 0 8px color-mix(in srgb, var(--ring), transparent 45%));
    }}
    .time {{
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
      font-size: clamp(2rem, 7vw, 3rem);
      font-weight: 700;
      letter-spacing: 0.04em;
    }}
    .controls {{ display: flex; gap: 10px; justify-content: center; margin-top: 14px; flex-wrap: wrap; }}
    button {{
      border: 1px solid rgba(255,255,255,.2);
      border-radius: 999px;
      color: var(--fg);
      background: rgba(255,255,255,.08);
      padding: 10px 16px;
      cursor: pointer;
      font-size: .95rem;
    }}
    button:hover {{ background: rgba(255,255,255,.14); }}
    .ab {{ margin-top: 12px; color: var(--muted); font-size: .85rem; }}
  </style>
</head>
<body data-variant=\"{variant}\">
  <canvas id=\"fx\"></canvas>
  <section class=\"card\">
    <div class=\"phase\" id=\"phase\">集中時間</div>
    <div class=\"timer-wrap\">
      <svg viewBox=\"0 0 320 320\" role=\"img\" aria-label=\"残り時間\">
        <circle class=\"track\" cx=\"160\" cy=\"160\" r=\"140\"></circle>
        <circle id=\"progress\" class=\"progress\" cx=\"160\" cy=\"160\" r=\"140\"></circle>
      </svg>
      <div id=\"time\" class=\"time\">25:00</div>
    </div>
    <div class=\"controls\">
      <button id=\"startPause\" type=\"button\">開始</button>
      <button id=\"reset\" type=\"button\">リセット</button>
    </div>
    <div class=\"ab\">A/Bテスト: variant={variant.upper()}（A: 背景エフェクト強 / B: 背景エフェクト弱）</div>
  </section>

<script>
(() => {{
  const focusDuration = {FOCUS_SECONDS};
  const breakDuration = {BREAK_SECONDS};
  const state = {{
    isFocus: true,
    isRunning: false,
    remainingMs: focusDuration * 1000,
    phaseEndAt: 0,
    lastTick: performance.now(),
    variant: document.body.dataset.variant || 'a'
  }};

  const phaseEl = document.getElementById('phase');
  const timeEl = document.getElementById('time');
  const progressEl = document.getElementById('progress');
  const startPauseBtn = document.getElementById('startPause');
  const resetBtn = document.getElementById('reset');

  const radius = 140;
  const circumference = 2 * Math.PI * radius;
  progressEl.style.strokeDasharray = String(circumference);

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const lerp = (a, b, t) => Math.round(a + (b - a) * clamp(t, 0, 1));

  function getColor(total, remaining) {{
    const elapsedRatio = 1 - clamp(remaining / total, 0, 1);
    const blue = [59,130,246], yellow = [234,179,8], red = [239,68,68];
    if (elapsedRatio < 0.5) {{
      const t = elapsedRatio / 0.5;
      return [lerp(blue[0], yellow[0], t), lerp(blue[1], yellow[1], t), lerp(blue[2], yellow[2], t)];
    }}
    const t = (elapsedRatio - 0.5) / 0.5;
    return [lerp(yellow[0], red[0], t), lerp(yellow[1], red[1], t), lerp(yellow[2], red[2], t)];
  }}

  function formatTime(ms) {{
    const total = Math.ceil(ms / 1000);
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${{String(m).padStart(2, '0')}}:${{String(s).padStart(2, '0')}}`;
  }}

  function phaseTotalSeconds() {{
    return state.isFocus ? focusDuration : breakDuration;
  }}

  function syncView() {{
    const totalSec = phaseTotalSeconds();
    const remainingSec = clamp(state.remainingMs / 1000, 0, totalSec);
    const offset = {progress_offset.__name__}(totalSec, remainingSec, circumference);
    progressEl.style.strokeDashoffset = String(offset);

    const [r,g,b] = getColor(totalSec, remainingSec);
    const color = `rgb(${{r}}, ${{g}}, ${{b}})`;
    document.documentElement.style.setProperty('--ring', color);
    progressEl.style.stroke = color;

    phaseEl.textContent = state.isFocus ? '集中時間' : '休憩時間';
    timeEl.textContent = formatTime(state.remainingMs);
  }}

  function progress_offset(total, remaining, c) {{
    if (total <= 0) return c;
    const ratio = clamp(remaining / total, 0, 1);
    return c * (1 - ratio);
  }}

  function switchPhase() {{
    state.isFocus = !state.isFocus;
    state.remainingMs = (state.isFocus ? focusDuration : breakDuration) * 1000;
    if (state.isRunning) state.phaseEndAt = performance.now() + state.remainingMs;
  }}

  function tick(now) {{
    if (state.isRunning) {{
      state.remainingMs = Math.max(0, state.phaseEndAt - now);
      if (state.remainingMs <= 0) {{
        switchPhase();
      }}
    }}
    syncView();
    drawFx(now);
    requestAnimationFrame(tick);
  }}

  startPauseBtn.addEventListener('click', () => {{
    if (!state.isRunning) {{
      state.isRunning = true;
      state.phaseEndAt = performance.now() + state.remainingMs;
      startPauseBtn.textContent = '一時停止';
    }} else {{
      state.isRunning = false;
      startPauseBtn.textContent = '再開';
    }}
  }});

  resetBtn.addEventListener('click', () => {{
    state.isFocus = true;
    state.isRunning = false;
    state.remainingMs = focusDuration * 1000;
    startPauseBtn.textContent = '開始';
    syncView();
  }});

  // 背景エフェクト（A: 粒子+波紋 / B: 低密度粒子）
  const canvas = document.getElementById('fx');
  const ctx = canvas.getContext('2d');
  let w = 0, h = 0, particles = [];

  function resize() {{
    w = canvas.width = window.innerWidth;
    h = canvas.height = window.innerHeight;
    particles = Array.from({{ length: state.variant === 'a' ? 60 : 20 }}, () => ({{
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 2 + 1
    }}));
  }}
  window.addEventListener('resize', resize);
  resize();

  function drawFx(now) {{
    ctx.clearRect(0, 0, w, h);
    if (!state.isFocus) return;

    const alpha = state.variant === 'a' ? 0.8 : 0.35;
    for (const p of particles) {{
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
      if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;
      ctx.beginPath();
      ctx.fillStyle = `rgba(120, 170, 255, ${{alpha}})`;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }}

    if (state.variant === 'a') {{
      const t = (now / 1000) % 4;
      const base = Math.min(w, h) * 0.17;
      for (let i = 0; i < 3; i++) {{
        const r = base + ((t + i * 1.3) % 4) * 90;
        ctx.beginPath();
        ctx.strokeStyle = `rgba(120,170,255,${{0.14 - i * 0.03}})`;
        ctx.lineWidth = 1.3;
        ctx.arc(w * 0.5, h * 0.5, r, 0, Math.PI * 2);
        ctx.stroke();
      }}
    }}
  }}

  syncView();
  requestAnimationFrame(tick);
}})();
</script>
</body>
</html>
"""


class _PomodoroHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path not in ("/", "/index.html"):
            self.send_error(404, "Not Found")
            return

        variant = parse_qs(parsed.query).get("variant", ["a"])[0]
        content = build_html(variant=variant).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def run_server(port: int = 8000) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), _PomodoroHandler)
    print(f"Pomodoro timer: http://127.0.0.1:{port} (A/B: ?variant=a|b)")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
