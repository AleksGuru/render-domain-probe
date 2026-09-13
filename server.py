import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

PAYLOAD = bytes(range(256)) * 4096
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
PAGE = Path(__file__).with_name('index.html').read_bytes()

class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        host = self.headers.get('Host', '').lower().split(':', 1)[0]
        if host in {'disrupt-radar.app', 'render-test.disrupt-radar.app'}:
            # Fixed destination: never trust a request-supplied host or scheme.
            target = urlsplit(self.path)
            location = 'https://disrupt-radar.up.railway.app/' + target.path.lstrip('/')
            if target.query:
                location += '?' + target.query
            self.send_response(302)
            self.send_header('Location', location)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        path = urlsplit(self.path).path
        if path == '/':
            self.respond(PAGE, 'text/html; charset=utf-8')
        elif path == '/health':
            self.respond(json.dumps({'ok': True, 'bytes': len(PAYLOAD), 'sha256': DIGEST}).encode(), 'application/json')
        elif path == '/payload':
            self.respond(PAYLOAD, 'application/octet-stream')
        else:
            self.respond(b'Not found', 'text/plain', 404)

    def respond(self, body, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try:
            if self.command != 'HEAD':
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def log_message(self, fmt, *args):
        # Do not log visitor IPs or request query strings.
        pass

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()
