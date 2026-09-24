# Disrupt Radar Render ingress proxy

This existing Render service terminates browser ingress for `disrupt-radar.app`
and transparently proxies application requests to Railway. The address bar stays
on `.app`. Application, database, workers and outgoing provider calls stay on
Railway. No application credentials are installed here.

## Runtime

- Build: `bash build.sh`; start: `python server.py`.
- Render health check: `/__proxy/health`; edge caching: **None**.
- Caddy **2.11.4** official release archive, pinned SHA-512 verified at build.
  Supports Render Linux amd64 and local macOS arm64; fails closed otherwise.
- Render handles public HTTPS; Caddy listens on `$PORT` (default 10000), admin off.
- Upstream DNS hostname: `disrupt-radar.up.railway.app`, with TLS verification,
  SNI and Host `disrupt-radar.app`. Preserve the Railway custom-domain association
  and certificate. Never point the upstream DNS at `.app`: that loops to Render.
- Forwarded host and protocol are overwritten to `.app` and `https`.
- Native Caddy proxy preserves methods, query, bodies, cookies, response statuses,
  streams and upgrades. No proxy cache or access log; request-bearing error logs
  disabled. Response-header timeout 420 seconds, connection timeout 10 seconds.
- Aliases `render-domain-probe.onrender.com` and `render-test.disrupt-radar.app`
  redirect application routes to `.app`; they do not create parallel sessions.
- `/__proxy/health` returns local process status, Git commit, payload size/digest.
  It does **not** claim Railway readiness. `/api/health/ready` checks the app.
- `/__proxy/payload` is exactly 1 MiB, no-store; SHA-256
  `fbbab289f7f94b25736c58be46a994c441fd02552cc6022352e3d86d2fab7c83`.

## Verification

Run `bash build.sh` and `python3 test_proxy.py`. Isolated fake-origin tests cover
methods/body/query, Host/forwarded-header overwrite, cookie request and duplicate
Set-Cookie response preservation, no-store, streaming, diagnostics and host routing.
TLS is verified separately by proxying the actual Railway health/homepage.

After deploy verify the exact Git commit is Live, custom-domain HTTP 200 without
Location, full HTML/static assets, 1 MiB digest, application health and cookie/API
flow. Russian probe HTTP 200 alone does not prove full mobile-browser completion:
Globalping truncates bodies at 10,000 decoded characters. Test real Russian mobile
and fixed networks without VPN when a tester is available. Render uses Cloudflare
at its edge, so prior success with a short redirect is not sufficient proof.

## Rollback

Set `PROXY_MODE=redirect` and redeploy the same revision. The preserved Python
redirect server returns the previous 302 to Railway and supports the new health
path. To roll back via Render's previous deploy artifact, restore its blank/TCP
health-check configuration and original build command `python -m py_compile server.py`
if rebuilding an old revision. Do not restore the previously failing Railway DNS
edge as a proxy rollback. Keep current Render DNS and Railway verification TXT.

## Session boundary

Railway-hostname cookies cannot transfer to `.app`. Users who signed in on the
Railway address may need to sign in on `.app`; existing `.app` cookies continue
being forwarded. Account storage and signing/encryption configuration are unchanged.

References: [Caddy reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[release](https://github.com/caddyserver/caddy/releases/tag/v2.11.4),
[Render deploys](https://render.com/docs/deploys),
[Render health checks](https://render.com/docs/health-checks).
