"""Isolated contract test against a local fake origin; no application data used."""
import hashlib
import http.client
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import unittest
import server

ROOT = Path(__file__).resolve().parent

def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]

class Origin(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.end_headers()
            self.wfile.write(b'data: first\n\n'); self.wfile.flush()
            time.sleep(1)
            self.wfile.write(b'data: last\n\n')
            return
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        data = json.dumps({'method': self.command, 'path': self.path,
            'headers': dict(self.headers), 'body': body.decode()}).encode()
        self.send_response(201)
        self.send_header('Set-Cookie', 'a=one; Path=/; Secure; HttpOnly; SameSite=Lax')
        self.send_header('Set-Cookie', 'b=two; Path=/; Secure; HttpOnly; SameSite=Lax')
        self.send_header('Cache-Control', 'private, no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)
    do_HEAD = do_POST = do_PATCH = do_DELETE = do_PUT = do_GET
    def log_message(self, *args): pass

class ProxyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.prepare()
        cls.origin = ThreadingHTTPServer(('127.0.0.1', 0), Origin)
        threading.Thread(target=cls.origin.serve_forever, daemon=True).start()
        cls.port = free_port()
        cfg = (ROOT / 'Caddyfile').read_text().replace('https://disrupt-radar.up.railway.app', f'http://127.0.0.1:{cls.origin.server_port}').replace('tls_server_name disrupt-radar.app', '')
        cls.temp = tempfile.TemporaryDirectory()
        config = Path(cls.temp.name) / 'Caddyfile'; config.write_text(cfg)
        cls.proc = subprocess.Popen([str(ROOT/'bin/caddy'),'run','--config',str(config),'--adapter','caddyfile'], env={**os.environ,'PORT':str(cls.port)}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(100):
            try:
                with socket.create_connection(('127.0.0.1', cls.port), timeout=.1): break
            except OSError: time.sleep(.05)
        else: raise RuntimeError('Caddy failed to start')
    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate(); cls.proc.wait(timeout=5)
        cls.origin.shutdown(); cls.origin.server_close(); cls.temp.cleanup()
    def request(self, method, path, host='disrupt-radar.app', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        conn.request(method,path,body=body,headers={'Host':host,**(headers or {})})
        response = conn.getresponse(); data = response.read(); conn.close()
        return response, data
    def test_methods_origin_cookies_and_query(self):
        for method in ['GET','POST','PATCH','PUT','DELETE']:
            response, data = self.request(method,'/api/test?q=a%2Fb','disrupt-radar.app','sample',{'Cookie':'session=test','X-Forwarded-Host':'evil.example','X-Forwarded-Proto':'http','Origin':'https://disrupt-radar.app'})
            result = json.loads(data); headers={k.lower():v for k,v in result['headers'].items()}
            self.assertEqual(response.status,201); self.assertEqual(result['method'],method)
            self.assertEqual(result['path'],'/api/test?q=a%2Fb'); self.assertEqual(result['body'],'sample')
            self.assertEqual(headers['host'],'disrupt-radar.app'); self.assertEqual(headers['x-forwarded-host'],'disrupt-radar.app')
            self.assertEqual(headers['x-forwarded-proto'],'https'); self.assertEqual(headers['cookie'],'session=test')
            self.assertEqual(len(response.headers.get_all('Set-Cookie')),2)
            self.assertEqual(response.getheader('Cache-Control'),'private, no-store')
    def test_diagnostics_and_hosts(self):
        response, data = self.request('GET','/__proxy/payload')
        self.assertEqual(len(data),1048576)
        self.assertEqual(hashlib.sha256(data).hexdigest(),'fbbab289f7f94b25736c58be46a994c441fd02552cc6022352e3d86d2fab7c83')
        response, data = self.request('HEAD','/__proxy/payload'); self.assertEqual(data,b'')
        response, _ = self.request('GET','/a?q=1','render-domain-probe.onrender.com')
        self.assertEqual(response.getheader('Location'),'https://disrupt-radar.app/a?q=1')
        response, _ = self.request('GET','/','evil.example'); self.assertEqual(response.status,421)
        response, data = self.request('GET','/__proxy/health'); self.assertTrue(json.loads(data)['ok'])
    def test_streaming(self):
        conn=http.client.HTTPConnection('127.0.0.1', self.port,timeout=3)
        started=time.monotonic(); conn.request('GET','/stream',headers={'Host':'disrupt-radar.app'})
        response=conn.getresponse(); self.assertEqual(response.read(13),b'data: first\n\n')
        self.assertLess(time.monotonic()-started,.8)
        self.assertEqual(response.read(),b'data: last\n\n'); conn.close()

if __name__ == '__main__': unittest.main(verbosity=2)
