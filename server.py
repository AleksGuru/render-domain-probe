"""Render entrypoint: diagnostics preparation, then exec the pinned Caddy binary."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def prepare():
    runtime = ROOT / '.runtime'
    runtime.mkdir(exist_ok=True)
    payload = bytes(range(256)) * 4096
    (runtime / 'payload').write_bytes(payload)
    revision = os.environ.get('RENDER_GIT_COMMIT')
    if not revision:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    (runtime / 'health').write_text(json.dumps({
        'ok': True, 'mode': 'reverse-proxy', 'commit': revision,
        'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(),
    }) + '\n')
    os.environ['DIAGNOSTIC_ROOT'] = str(runtime)

if __name__ == '__main__':
    os.chdir(ROOT)
    if os.environ.get('PROXY_MODE') == 'redirect' and '--validate' not in sys.argv:
        os.execv(sys.executable, [sys.executable, str(ROOT / 'redirect_server.py')])
    prepare()
    action = 'validate' if '--validate' in sys.argv else 'run'
    binary = str(ROOT / 'bin/caddy')
    os.execv(binary, [binary, action, '--config', str(ROOT / 'Caddyfile'), '--adapter', 'caddyfile'])
