import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

def start_debug_server(ns, host="0.0.0.0", port=8080):

    class Handler(BaseHTTPRequestHandler):

        def send_json(self, data):
            body = json.dumps(data, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_text(self, text, code=200):
            body = text.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            # ----------------------------
            # STATE JSON
            # ----------------------------
            if path == "/state":
                with ns.lock:
                    nav = ns.nav_agent
                    mp = ns.map_nav

                    snapshot = {
                        "MapNavigator": {
                            "currentLocation": mp.currentLocation,
                            "destination": mp.destination,
                            "WalkPath_length": len(nav.path) if nav.path else 0
                        },
                        "Navigation": {
                            "state": ns.state,
                            "mode": nav.mode,
                            "index": nav.index,
                            "target": nav.target,
                            "turn_angle": nav.turn_angle,
                            "wrong_dir_counter": nav.wrong_dir_counter,
                            "offroute_counter": nav.offroute_counter,
                            "Distance To Target":nav.dist_to_target
                        },
                        "System": {
                            "navigating": ns.navigating,
                            "ultrasonic": ns.ultrasonicLine
                        }
                    }

                self.send_json(snapshot)
                return

            # ----------------------------
            # SET PARAMETERS
            # ----------------------------
            if path == "/set":
                if not qs:
                    self.send_text("Missing parameter", 400)
                    return

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
                            self.send_text("Destination updated")

                        elif key == "navigating":
                            ns.navigating = value == "1"
                            self.send_text("Navigation toggled")

                        elif key == "recalculate":
                            nav.updatePath()
                            self.send_text("Route recalculated")

                        else:
                            self.send_text("Unknown parameter", 400)

                    except Exception as e:
                        self.send_text(str(e), 400)

                return

            # ----------------------------
            # UI PAGE
            # ----------------------------
            if path == "/" or path == "/ui":
                html = """
                <html>
                <head>
                <title>DoggyStick Control</title>
                <style>
                body { background:#1e1e1e; color:#eee; font-family:Arial; padding:20px;}
                h2 { border-bottom:1px solid #444; }
                pre { background:#111; padding:15px; border-radius:10px; }
                input { padding:8px; margin:5px; border-radius:8px; border:none;}
                button { padding:8px 15px; border-radius:8px; border:none; cursor:pointer;}
                button:hover { opacity:0.8; }
                .box { margin-bottom:20px; }
                </style>
                </head>
                <body>

                <h1>🚗 DoggyStick Debug Panel</h1>

                <div class="box">
                <h2>Live State</h2>
                <pre id="state">Loading...</pre>
                </div>

                <div class="box">
                <h2>Set Destination</h2>
                <input id="dest" placeholder="47.5843,-122.1481">
                <button onclick="setParam('destination', dest.value)">Set</button>
                </div>

                <div class="box">
                <h2>Navigation Control</h2>
                <button onclick="setParam('navigating','1')">Start</button>
                <button onclick="setParam('navigating','0')">Stop</button>
                <button onclick="setParam('recalculate','1')">Recalculate Route</button>
                </div>

                <script>
                async function refresh(){
                    const r = await fetch('/state');
                    const j = await r.json();
                    document.getElementById('state').innerText =
                        JSON.stringify(j,null,2);
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
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
                return

            self.send_text("Not Found", 404)

        def log_message(self, format, *args):
            return

    print(f"[WEB] Running at http://{host}:{port}/ui")
    HTTPServer((host, port), Handler).serve_forever()