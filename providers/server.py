from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial


HOST = "0.0.0.0"
PORT = 8090
OUTPUT_DIR = "output"


def start_server():
    handler = partial(SimpleHTTPRequestHandler, directory=OUTPUT_DIR)

    server = ThreadingHTTPServer((HOST, PORT), handler)

    print(f"Serving Doodah TV files at http://{HOST}:{PORT}")
    print(f"Serving directory: {OUTPUT_DIR}")

    server.serve_forever()