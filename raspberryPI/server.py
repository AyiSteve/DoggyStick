import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

def build_snapshot(ns):
    """
    Return a JSON-serializable snapshot of important runtime fields.
    Keep this small + safe (no huge objects).
    """
    nav = ns.nav_agent
    mp = ns.map_nav

    snap = {
        "navigating": ns.navigating,
        "state": ns.state,
        "ultrasonicLine": ns.ultrasonicLine,

        "gps_current": mp.currentLocation,
        "destination": mp.destination,

        "nav_index": getattr(nav, "index", None),
        "nav_target": getattr(nav, "target", None),
        "turn_angle": getattr(nav, "turn_angle", None),
        "wrong_dir_counter": getattr(nav, "wrong_dir_counter", None),
        "offroute_counter": getattr(nav, "offroute_counter", None),

        "path_len": (len(nav.path) if nav.path else 0),
    }
    return snap


def try_set_param(ns, key, value):
    """
    Very small 'setter' interface for debugging.
    Add/remove fields as you need.
    """
    if key == "navigating":
        # /set?navigating=1 or 0
        ns.navigating = value in ("1", "true", "True", "yes", "on")
        return True, f"navigating set to {ns.navigating}"

    if key == "destination":
        # /set?destination=47.5843,-122.1481
        parts = value.split(",")
        if len(parts) != 2:
            return False, "destination must be 'lat,lng'"
        lat = float(parts[0].strip())
        lng = float(parts[1].strip())
        ns.map_nav.updateDestination((lat, lng))
        # IMPORTANT: build a path immediately
        ns.nav_agent.updatePath()
        ns.navigating = True
        return True, f"destination set to ({lat},{lng}) and path updated"

    if key == "offroute_max":
        # example: if you later add nav.offroute_max
        # nav.offroute_max = float(value)
        return False, "offroute_max not implemented in your Navigation class yet"

    return False, f"Unknown param '{key}'"


def start_debug_server(ns, host="127.0.0.1", port=8080):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, content_type, body_bytes):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            if path == "/" or path == "/ui":
                html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>DoggyStick Debug</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Arial; margin: 16px; }}
    pre {{ background: #111; color: #0f0; padding: 12px; border-radius: 10px; overflow:auto; }}
    .row {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
    input {{ padding:8px; border-radius:8px; border:1px solid #ccc; }}
    button {{ padding:8px 12px; border-radius:8px; border:1px solid #ccc; cursor:pointer; }}
    small {{ color:#555; }}
  </style>
</head>
<body>
  <h2>DoggyStick Debug Dashboard</h2>
  <div class="row">
    <button onclick="refresh()">Refresh</button>
    <small>Auto-refresh every 1s</small>
  </div>

  <h3>Set destination</h3>
  <div class="row">
    <input id="dest" placeholder="lat,lng  (e.g. 47.5843,-122.1481)" size="40" />
    <button onclick="setDest()">Set</button>
  </div>

  <h3>Toggle navigating</h3>
  <div class="row">
    <button onclick="setNav(1)">Start</button>
    <button onclick="setNav(0)">Stop</button>
  </div>

  <h3>Snapshot</h3>
  <pre id="out">loading...</pre>

<script>
async function refresh() {{
  const r = await fetch('/state');
  const j = await r.json();
  document.getElementById('out').textContent = JSON.stringify(j, null, 2);
}}

async function setNav(v) {{
  const r = await fetch(`/set?navigating=${{v}}`);
  await refresh();
}}

async function setDest() {{
  const v = document.getElementById('dest').value.trim();
  if (!v) return;
  await fetch(`/set?destination=${{encodeURIComponent(v)}}`);
  await refresh();
}}

refresh();
setInterval(refresh, 1000);
</script>
</body>
</html>"""
                self._send(200, "text/html; charset=utf-8", html.encode("utf-8"))
                return

            if path == "/state":
                with ns.lock:
                    snap = build_snapshot(ns)
                body = json.dumps(snap, indent=2).encode("utf-8")
                self._send(200, "application/json; charset=utf-8", body)
                return

            if path == "/set":
                # /set?param=value  (we accept exactly one)
                if not qs:
                    self._send(400, "text/plain; charset=utf-8", b"Missing query param\n")
                    return

                # take first key/value
                key = next(iter(qs.keys()))
                value = qs[key][0]

                with ns.lock:
                    ok, msg = try_set_param(ns, key, value)

                code = 200 if ok else 400
                self._send(code, "text/plain; charset=utf-8", (msg + "\n").encode("utf-8"))
                return

            self._send(404, "text/plain; charset=utf-8", b"Not found\n")

        def log_message(self, format, *args):
            # silence default request logs
            return

    httpd = HTTPServer((host, port), Handler)
    print(f"[WEB] Debug server running at http://{host}:{port}/ui")
    httpd.serve_forever()