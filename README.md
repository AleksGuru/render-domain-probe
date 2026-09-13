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

Activated 2026-09-13: Render deploy `dep-dajef4e7bikc73borla0`, commit
`a8e198d`. Railway DNS ANAME was updated as described above. Verified normal
HTTPS GET follows one redirect to the Railway homepage with HTTP 200 and valid
TLS; HEAD `/projects?source=domain-check` returns 302 with path/query intact.
The root domain was Verified in Render and HTTPS issuance completed. The
existing RF test was reported by the owner on the test subdomain; final root
access should also be checked on the owner's RF networks without VPN.
