#!/usr/bin/env bash
set -euo pipefail
umask 077
export GIT_TERMINAL_PROMPT=0
export GIT_SSH_COMMAND='ssh -i /etc/rex-status/publish_key -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=/etc/rex-status/github_known_hosts -o ConnectTimeout=12 -p 443'
state=/var/lib/rex-status/pulse
mkdir -p "$state"
exec 9>/var/lib/rex-status/publish.lock
flock -n 9 || exit 0
if ! git -C "$state" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$state" init --initial-branch=pulse --quiet
  git -C "$state" config user.name 'REX Status Monitor'
  git -C "$state" config user.email 'status@rexcorp.space'
  git -C "$state" remote add origin ssh://git@ssh.github.com:443/IliaBebebe/rex-status.git
fi
# Restore the last published heartbeat branch when rebuilding the local state.
if git -C "$state" ls-remote --exit-code origin refs/heads/pulse >/dev/null 2>&1; then
  git -C "$state" fetch --quiet --depth=1 origin pulse
  git -C "$state" reset --quiet --hard FETCH_HEAD
fi
python3 /usr/local/lib/rex-status/collect_home.py > "$state/heartbeat.json.new"
python3 - "$state/heartbeat.json.new" <<'PY'
import json,sys
data=json.load(open(sys.argv[1]))
assert set(data)=={'schemaVersion','checkedAt','services'}
assert set(data['services'])=={'sticker','support','morning','flight','serverbot'}
assert set(data['services'].values()) <= {'operational','outage','unknown'}
PY
mv "$state/heartbeat.json.new" "$state/heartbeat.json"
git -C "$state" add -- heartbeat.json
git -C "$state" commit --quiet -m 'Update public connection checks'
git -C "$state" push --quiet origin HEAD:refs/heads/pulse
echo 'Public bot checks published'
