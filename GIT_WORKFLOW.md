# Git workflow

- Local: `C:\Users\user\Desktop\REX_PROJECTS\rex-status`
- URL: https://status.rexcorp.space/
- `origin`: https://github.com/IliaBebebe/rex-status.git
- `vps`: rex-home-deploy:/srv/git/rex-status.git
- Source branch `main`; branch `pulse` contains only public heartbeat JSON, written by the home collector.
- Run `python -m unittest discover -s tests`, `node --check web/app.js`, and `python build.py --no-probes` before source publication.
- Push source to `origin/main` to publish; mirror source with `git push vps main`.
- Observe GitHub Actions and the actual HTTPS site after deploying. DNS must remain unproxied for independence from the Cloudflare visitor path.
- Do not publish `.env`, tokens, SSH private keys, logs, source backup archives or databases. Do not modify the heartbeat branch from a source deployment.
- To restore source, revert a specific source commit and publish. To disable telemetry, stop only `rex-status-publish.timer`. Never restart unrelated services.
