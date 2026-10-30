#!/usr/bin/env python3
"""Read-only local probes. Publish only allowlisted IDs and coarse states."""
import concurrent.futures, json, subprocess, urllib.request
from datetime import datetime, timezone
from pathlib import Path

BOTS = {
    'sticker':('telegram-sticker','TELEGRAM_TOKEN','telegram-sticker'),
    'support':('usupovo-bot','BOT_TOKEN','usupovo-bot'),
    'morning':('good-morning-bot','TELEGRAM_TOKEN','good-morning-bot'),
    'flight':('su208-tracker','TG_BOT_TOKEN','su208-bot'),
    'serverbot':('server-admin-bot','BOT_TOKEN','server-admin-bot'),
}

def check(item):
    identifier, (project, key, unit) = item
    try:
        values = {}
        for line in (Path('/opt')/project/'.env').read_text().splitlines():
            if '=' in line and not line.lstrip().startswith('#'):
                name, value = line.split('=',1)
                values[name.strip()] = value.strip().strip('"').strip("'")
        active = subprocess.run(['systemctl','is-active','--quiet',unit],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode == 0
        if not active:
            return identifier, 'outage'
        for attempt in range(2):
            try:
                url = 'http://127.0.0.1:8445/bot'+values[key]+'/getMe'
                with urllib.request.urlopen(url,timeout=12) as response:
                    if json.load(response).get('ok'):
                        return identifier, 'operational'
            except Exception:
                pass
        return identifier, 'outage'
    except Exception:
        # No raw exceptions/URLs: they may include Telegram credentials.
        return identifier, 'unknown'

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        states = dict(pool.map(check,BOTS.items()))
    result = {'schemaVersion':1,'checkedAt':datetime.now(timezone.utc).isoformat(),'services':states}
    print(json.dumps(result,separators=(',',':')))
