# REX Status

Public user-facing status page: https://status.rexcorp.space/

REX Corp branding uses the original corporate logo and homepage palette. See [BRANDING.md](BRANDING.md) before changing identity assets or theme colours.

Source: `C:\Users\user\Desktop\REX_PROJECTS\rex-status`.
Production is static GitHub Pages, independent of the home server, Windows and Cloudflare's HTTP proxy. Cloudflare is DNS-only for this hostname.

## What a status proves

- The external workflow checks 18 public pages. Expected sign-in redirects or 401 responses are valid only for the configured protected sites. This proves HTTP reachability from GitHub's network, not every feature or reachability from every ISP.
- An active regional access incident keeps affected sites **limited**, even if the HTTP probe succeeds. Edit `incidents.json` only after actual user verification; automatic checks cannot resolve it.
- Five ecosystem bots are checked on home Ubuntu with service state plus read-only Telegram `getMe`. No passwords, bot responses, usernames, logs, IPs or tokens enter the public snapshot.
- A heartbeat older than 35 minutes becomes unknown. Browser snapshots older than 45 minutes become unknown. No fabricated uptime percentages or historical bars.
- Scope excludes the game server and its administration bot.

## Update flow

Home `rex-status-publish.timer` produces the bot heartbeat on branch `pulse` around every 15 minutes. The deploy key is restricted to this repository. It is stored only in `/etc/rex-status/publish_key`, never in Git. The source checkout does not contain it.

GitHub Actions on `main`, manual dispatch, or a 15-minute schedule reads that heartbeat, performs external checks, renders HTML + JSON and publishes Pages. Schedules may be delayed by GitHub. When the home server is unavailable, the independent external checks and status page continue; bot states become unknown after expiry.

After publication, the workflow tests the custom hostname with strict TLS verification and enables HTTPS enforcement once the certificate is ready. Pending certificate provisioning is retried on later scheduled runs.

## Local checks

```powershell
python -m unittest discover -s tests
node --check web/app.js
python build.py --no-probes
python -m http.server 4873 --directory dist --bind 127.0.0.1
```

Build with real probes: `python build.py --heartbeat <sanitized-heartbeat.json>`.
No dependency installation, backend framework, database, analytics or cookies.

## Incident changes

Update title, advice and dated messages in `incidents.json`, commit and push `main`. Set `active=false` only when confirmed resolved. Keep existing messages factual and do not invent event times. User-facing copy does not disclose private infrastructure or access credentials.

## Hosting

- Repository: `https://github.com/IliaBebebe/rex-status`
- Branch: `main`, telemetry branch: `pulse`
- Pages custom domain: `status.rexcorp.space`; GitHub issues/renews HTTPS.
- Cloudflare record: DNS-only CNAME `status` → `iliabebebe.github.io`.
- Home collector: `/usr/local/lib/rex-status/collect_home.py`; publisher: `/usr/local/sbin/rex-status-publish`.
- Unit: `rex-status-publish.service`, timer `rex-status-publish.timer`.
- Bare source mirror: `rex-home-deploy:/srv/git/rex-status.git`.
- This hostname does not need a home Nginx site or Cloudflare Tunnel ingress.

GitHub Pages public repository hosting does not require a paid plan or card. No paid Actions runner or additional billing is configured.
