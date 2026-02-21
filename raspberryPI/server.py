import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

def start_debug_server(ns, host="0.0.0.0", port=8080):

    class Handler(BaseHTTPRequestHandler):

        def _send(self, code, content_type, body):
            body_bytes = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            if path == "/state":
                with ns.lock:
                    nav = ns.nav_agent
                    mp = ns.map_nav

                    snapshot = {
                        "MapNavigator": {
                            "currentLocation": mp.currentLocation,
                            "destination": mp.destination,
                            "path_len": len(nav.path) if nav.path else 0
                        },
                        "Navigation": {
                            "state": ns.state,
                            "mode": nav.mode,
                            "index": nav.index,
                            "target": nav.target,
                            "turn_angle": nav.turn_angle,
                            "wrong_dir_counter": nav.wrong_dir_counter,
                            "offroute_counter": nav.offroute_counter,
                            "offroute_max_dist": nav.offroute_max_dist,
                            "offroute_window": nav.offroute_window,
                            "target_reached_dist": nav.target_reached_dist,
                            "wrong_dir_threshold_low": nav.wrong_dir_threshold_low,
                            "wrong_dir_threshold_high": nav.wrong_dir_threshold_high,
                            "navigating": ns.navigating
                        }
                    }

                self._send(200, "application/json", json.dumps(snapshot, indent=2))
                return

            if path == "/set":
                key = list(qs.keys())[0]
                value = qs[key][0]

                with ns.lock:
                    nav = ns.nav_agent
                    mp = ns.map_nav

                    try:
                        if key == "destination":
                            lat, lng = map(float, value.split(","))
                            mp.updateDestination((lat, lng))
                            nav.updatePath()
                            ns.navigating = True

                        elif hasattr(nav, key):
                            setattr(nav, key, type(getattr(nav, key))(value))

                        elif key == "navigating":
                            ns.navigating = value == "1"

                        else:
                            return self._send(400, "text/plain", "Unknown parameter")

                    except Exception as e:
                        return self._send(400, "text/plain", str(e))

                self._send(200, "text/plain", "Updated")
                return

            if path == "/" or path == "/ui":
                html = """
                <html>
                <head>
                <title>DoggyStick Control Panel</title>
                <style>
                body { font-family: Arial; background:#1e1e1e; color:white; padding:20px;}
                h2 { border-bottom:1px solid #444; }
                pre { background:#111; padding:15px; border-radius:10px; }
                input { padding:6px; margin:4px; border-radius:6px;}
                button { padding:6px 12px; border-radius:6px;}
                </style>
                </head>
                <body>

                <h2>Live State</h2>
                <pre id="out">Loading...</pre>

                <h2>Set Destination</h2>
                <input id="dest" placeholder="47.5843,-122.1481">
                <button onclick="setParam('destination', document.getElementById('dest').value)">Set</button>

                <h2>Navigation Parameters</h2>
                <input id="offdist" placeholder="offroute_max_dist">
                <button onclick="setParam('offroute_max_dist', offdist.value)">Update</button>

                <input id="window" placeholder="offroute_window">
                <button onclick="setParam('offroute_window', window.value)">Update</button>

                <input id="targetdist" placeholder="target_reached_dist">
                <button onclick="setParam('target_reached_dist', targetdist.value)">Update</button>

                <input id="wronglow" placeholder="wrong_dir_threshold_low">
                <button onclick="setParam('wrong_dir_threshold_low', wronglow.value)">Update</button>

                <input id="wronghigh" placeholder="wrong_dir_threshold_high">
                <button onclick="setParam('wrong_dir_threshold_high', wronghigh.value)">Update</button>

                <h2>Navigation Control</h2>
                <button onclick="setParam('navigating', '1')">Start</button>
                <button onclick="setParam('navigating', '0')">Stop</button>

                <script>
                async function refresh(){
                    let r = await fetch('/state');
                    let j = await r.json();
                    document.getElementById('out').innerText = JSON.stringify(j,null,2);
                }
                async function setParam(k,v){
                    await fetch('/set?'+k+'='+encodeURIComponent(v));
                    refresh();
                }
                setInterval(refresh,1000);
                refresh();
                </script>

                </body>
                </html>
                """
                self._send(200, "text/html", html)
                return

            self._send(404, "text/plain", "Not Found")

        def log_message(self, format, *args):
            return

    print(f"[WEB] Running on http://{host}:{port}/ui")
    HTTPServer((host, port), Handler).serve_forever()