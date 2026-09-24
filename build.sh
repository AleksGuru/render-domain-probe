#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p bin
python3 - <<'PY'
import hashlib, io, pathlib, platform, tarfile, urllib.request
assets = {
    ('Linux', 'x86_64'): ('linux_amd64', '8220d1f013b6f27510247b2360c9e0ca9f018feebd82515f07635318b34ff9777ccc8fd0b6e6f2486ce3a33fe389fbb7db12d05baa474f4587509fb4f5ebf1c9'),
    ('Darwin', 'arm64'): ('mac_arm64', '3190ae0df98b59ab4b6021556fa35adc3c526a4f3e138776b0eaec8a037cc26121cbbb1ad53453f565551b47d37d5ba4755e2c2c3652256737fe2ce9e53c8ec0'),
}
asset, expected = assets[(platform.system(), platform.machine())]
url = f'https://github.com/caddyserver/caddy/releases/download/v2.11.4/caddy_2.11.4_{asset}.tar.gz'
with urllib.request.urlopen(url, timeout=90) as response:
    archive = response.read()
if hashlib.sha512(archive).hexdigest() != expected:
    raise SystemExit('Caddy archive checksum mismatch')
with tarfile.open(fileobj=io.BytesIO(archive), mode='r:gz') as tar:
    binary = tar.extractfile('caddy').read()
path = pathlib.Path('bin/caddy')
path.write_bytes(binary)
path.chmod(0o755)
PY
python3 -m py_compile server.py redirect_server.py
python3 server.py --validate
