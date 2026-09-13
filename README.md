# Render custom-domain probe

Standalone, dependency-free Python service. No database, credentials, analytics or business data.

Run: `PORT=8080 python3 server.py`.

Endpoints: `/` diagnostic UI, `/health` JSON, `/payload` exactly 1 MiB binary. Responses use no-store. Browser checks SHA-256 and enforces a 45-second timeout per request. No automatic polling. Request logging is disabled.

Compare the Render hostname and custom hostname from the same Russian mobile/Wi-Fi networks with VPN disabled. A successful external probe alone does not demonstrate Russian-network accessibility. Free Render cold starts are a separate source of delay.

## Domain redirect

`disrupt-radar.app` and `render-test.disrupt-radar.app` return HTTP 302 to
`https://disrupt-radar.up.railway.app`, preserving path and query. Responses
are not cached. GET and HEAD are supported. The diagnostic endpoints remain
available on `render-domain-probe.onrender.com`. The browser address changes
to Railway; application and outgoing backend requests remain on Railway.

DNS cutover: Railway-managed ANAME `@` targets `render-domain-probe.onrender.com`.
Rollback: restore ANAME `@` to `eoj9a4jm.up.railway.app` (TTL 300). Preserve
the Railway verification TXT and existing Railway domain association.
