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
                            "Distance To Target":nav.dist_to_target,
                            "heading":nav.heading
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
                        elif key == "location":
                            lat, lng = map(float, value.split(","))

                            mp.updateCurrentLocation((lat, lng))

                            # also update heading reference so navigation behaves correctly
                            if nav.prevGPS is None:
                                nav.prevGPS = (lat, lng)

                            self.send_text("Current location updated")
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

                body{
                background:#0f172a;
                color:#e2e8f0;
                font-family:Arial;
                padding:30px;
                }

                h1{
                margin-bottom:25px;
                }

                .grid{
                display:grid;
                grid-template-columns:repeat(3,1fr);
                gap:20px;
                }

                .card{
                background:#1e293b;
                padding:20px;
                border-radius:12px;
                box-shadow:0 4px 10px rgba(0,0,0,0.4);
                }

                .card h3{
                margin-top:0;
                color:#38bdf8;
                }

                .value{
                font-size:22px;
                font-weight:bold;
                }

                input{
                padding:8px;
                border-radius:8px;
                border:none;
                margin-right:10px;
                }

                button{
                padding:8px 14px;
                border-radius:8px;
                border:none;
                cursor:pointer;
                margin-right:5px;
                background:#38bdf8;
                color:black;
                font-weight:bold;
                }

                button:hover{
                opacity:0.85;
                }

                pre{
                background:#020617;
                padding:10px;
                border-radius:8px;
                overflow:auto;
                max-height:250px;
                }

                .status-ok{color:#22c55e}
                .status-bad{color:#ef4444}

                </style>
                </head>

                <body>

                <h1>? DoggyStick Navigation Dashboard</h1>

                <div class="grid">

                <div class="card">
                <h3>Navigation State</h3>
                <div id="nav_state" class="value">--</div>
                <div>Angle: <span id="angle">--</span>�</div>
                <div>Heading: <span id="heading">--</span></div>
                </div>
                <div class="card">
                <h3>Set Current Location</h3>

                <input id="loc" placeholder="47.6555,-122.308">

                <button onclick="setParam('location',loc.value)">
                Update Location
                </button>

                </div>

                <div class="card">
                <h3>Target</h3>
                <div>Index: <span id="index">--</span></div>
                <div>Distance: <span id="dist">--</span> m</div>
                </div>

                <div class="card">
                <h3>System</h3>
                <div>Navigating: <span id="nav_active">--</span></div>
                </div>

                <div class="card">
                <h3>Ultrasonic</h3>
                <div>Front: <span id="front">--</span> cm</div>
                <div>Left: <span id="left">--</span> cm</div>
                <div>Right: <span id="right">--</span> cm</div>
                </div>

                <div class="card">
                <h3>Destination</h3>

                <input id="dest" placeholder="47.5843,-122.1481">

                <button onclick="setParam('destination',dest.value)">
                Set
                </button>

                </div>

                <div class="card">
                <h3>Controls</h3>

                <button onclick="setParam('navigating','1')">
                Start
                </button>

                <button onclick="setParam('navigating','0')">
                Stop
                </button>

                <button onclick="setParam('recalculate','1')">
                Recalculate
                </button>

                </div>

                </div>

                <br>

                <div class="card">
                <h3>Raw State</h3>
                <pre id="raw"></pre>
                </div>


                <script>

                async function refresh(){

                const r = await fetch('/state')
                const j = await r.json()

                document.getElementById("raw").innerText =
                JSON.stringify(j,null,2)

                document.getElementById("nav_state").innerText =
                j.Navigation.state

                document.getElementById("angle").innerText =
                j.Navigation.turn_angle.toFixed(1)

                document.getElementById("heading").innerText =
                j.Navigation.heading

                document.getElementById("index").innerText =
                j.Navigation.index

                document.getElementById("dist").innerText =
                j.Navigation["Distance To Target"]

                document.getElementById("nav_active").innerText =
                j.System.navigating

                if(j.System.ultrasonic){

                document.getElementById("front").innerText =
                j.System.ultrasonic.front.toFixed(1)

                document.getElementById("left").innerText =
                j.System.ultrasonic.left.toFixed(1)

                document.getElementById("right").innerText =
                j.System.ultrasonic.right.toFixed(1)

                }

                }

                async function setParam(k,v){
                await fetch('/set?'+k+'='+encodeURIComponent(v))
                refresh()
                }

                setInterval(refresh,500)
                refresh()

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