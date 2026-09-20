import http.server
import socketserver
import webbrowser
import os
import sys
import threading
import time
import socket
import functools

# Configure UTF-8 stdout if supported
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Resolve directory containing cinematic_pitch files
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(CURRENT_DIR, "index.html")):
    SERVE_DIR = CURRENT_DIR
elif os.path.exists(os.path.join(CURRENT_DIR, "cinematic_pitch", "index.html")):
    SERVE_DIR = os.path.join(CURRENT_DIR, "cinematic_pitch")
else:
    SERVE_DIR = CURRENT_DIR

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress noisy HTTP request logging for clean presentation terminal
        pass

def get_free_port():
    candidate_ports = [8088, 8888, 5500, 3000, 5173, 9000, 4200, 8081]
    for p in candidate_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                return p
            except OSError:
                continue
    # Fallback to OS assigned free port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def main():
    port = get_free_port()
    handler = functools.partial(QuietHandler, directory=SERVE_DIR)
    
    try:
        httpd = socketserver.TCPServer(('127.0.0.1', port), handler)
    except Exception as e:
        print(f"[ERROR] Failed to start local server on port {port}: {e}")
        print("You can open index.html directly in Chrome or Edge.")
        sys.exit(1)

    url = f"http://127.0.0.1:{port}/index.html"
    
    print("============================================================")
    print("  [AeroCPI + AeroGuide] Official SIH 2026 Pitch Presentation")
    print("  Team BUZZCODEX | Problem Statement: SIH26056 | Smart Automation")
    print(f"  Live Presentation at: {url}")
    print("  Keyboard: [<- / ->] Navigate | [1-6] Jump | [F] Fullscreen | [P] Download PPTX")
    print("  Press Ctrl+C to stop the runner.")
    print("============================================================")

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.5)
    print(f"Opening browser at {url} ...")
    webbrowser.open(url)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping pitch film server. Good luck at SIH 2026!")
        httpd.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    main()
