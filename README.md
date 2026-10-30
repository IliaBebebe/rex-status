# REX Corp Status

Public URL: https://status.rexcorp.space/

Production runs on home Ubuntu with Nginx and the existing Certbot wildcard certificate. GitHub stores source only; GitHub Pages and its workflow are disabled.

- Runtime source: `/opt/rex-status`; public root: `/var/www/rex-status`.
- Refresh: `rex-status-refresh.timer` every 15 minutes, service `rex-status-refresh.service`, script `/usr/local/sbin/rex-status-refresh`.
- Five bot connection checks are collected locally. Public website checks use the existing Linux transport via the service's `REX_STATUS_PROXY`; no Windows dependency.
- Known regional access restrictions remain an explicit incident. An HTTP 200 cannot resolve it. Telemetry expires rather than showing stale green states.
- DNS uses the existing home Cloudflare Tunnel; this website has the same regional connectivity limits as other REX websites.
- Original REX Corp logo and palette: see BRANDING.md. No game hosting is included.

Checks: `python -m unittest discover -s tests`; `node --check web/app.js`.

Source: `origin/main` on GitHub, mirror `vps/main` at `rex-home-deploy:/srv/git/rex-status.git`. Deploy reviewed source changes to `/opt/rex-status`, then run `systemctl start rex-status-refresh.service`. No dependencies or app server are required. Keep private credentials and runtime data outside Git.
