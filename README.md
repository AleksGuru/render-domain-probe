# Render custom-domain probe

Standalone, dependency-free Python service. No database, credentials, analytics or business data.

Run: `PORT=8080 python3 server.py`.

Endpoints: `/` diagnostic UI, `/health` JSON, `/payload` exactly 1 MiB binary. Responses use no-store. Browser checks SHA-256 and enforces a 45-second timeout per request. No automatic polling. Request logging is disabled.

Compare the Render hostname and custom hostname from the same Russian mobile/Wi-Fi networks with VPN disabled. A successful external probe alone does not demonstrate Russian-network accessibility. Free Render cold starts are a separate source of delay.
