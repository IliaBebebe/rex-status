"""Build a static, server-rendered status page with bounded public probes."""
import argparse, concurrent.futures, html, json, shutil, time, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path
from status_model import compose, LABELS, GROUPS

ROOT = Path(__file__).resolve().parent

def human_date(value):
    date = datetime.fromisoformat(value)
    months = ('января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря')
    return f'{date.day} {months[date.month-1]} {date.year}'

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None

def probe(service):
    opener = urllib.request.build_opener(NoRedirect)
    code = None
    for attempt in range(2):
        try:
            request = urllib.request.Request(service["url"], headers={"User-Agent":"REX-Status/1.0 (+https://status.rexcorp.space/)"})
            with opener.open(request, timeout=8) as response:
                code = response.status
                response.read(4096)
        except urllib.error.HTTPError as error:
            code = error.code
            error.close()
        except Exception:
            code = None
        if code in service["codes"]:
            break
        if attempt == 0:
            time.sleep(0.3)
    return service["id"], {"ok":code in service["codes"], "checkedAt":datetime.now(timezone.utc).isoformat()}

def service_html(item):
    esc = html.escape
    name = esc(item["name"])
    if item.get("url"):
        name = f'<a href="{esc(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{name}<span class="sr-only"> (откроется в новой вкладке)</span></a>'
    return f'<li class="service" data-group="{item["group"]}" data-status="{item["status"]}"><div class="service-info"><h3>{name}</h3><p>{esc(item["description"])}</p></div><div class="service-state"><span class="pill {item["status"]}"><span class="dot" aria-hidden="true"></span>{esc(item["label"])}</span><span class="service-note">{esc(item["note"])}</span></div></li>'

def incident_html(incidents):
    active = [i for i in incidents if i.get("active")]
    if not active:
        return '<p class="muted">Открытых сообщений о сбоях нет.</p>'
    blocks = []
    for incident in active:
        updates = ''.join(f'<li><time datetime="{u["date"]}">{human_date(u["date"])}</time><div><h4>{html.escape(u["title"])}</h4><p>{html.escape(u["text"])}</p></div></li>' for u in incident["updates"])
        blocks.append(f'<article class="incident"><div class="incident-top"><span class="incident-stage">{html.escape(incident["stage"])}</span><time datetime="{incident["date"]}">{human_date(incident["date"])}</time></div><h3>{html.escape(incident["title"])}</h3><p>{html.escape(incident["summary"])}</p><div class="advice"><strong>Что можно сделать сейчас</strong><p>{html.escape(incident["advice"])}</p></div><p>{html.escape(incident["unaffected"])}</p><details><summary>Ход работ</summary><ol class="timeline">{updates}</ol></details></article>')
    return ''.join(blocks)

def build(run_probes=True, heartbeat_path=None):
    services = json.loads((ROOT/'services.json').read_text(encoding='utf-8'))
    incidents = json.loads((ROOT/'incidents.json').read_text(encoding='utf-8'))
    heartbeat = {}
    if heartbeat_path and Path(heartbeat_path).is_file():
        try:
            heartbeat = json.loads(Path(heartbeat_path).read_text(encoding='utf-8'))
        except (ValueError, OSError):
            pass
    probes = {}
    if run_probes:
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            probes = dict(pool.map(probe, (s for s in services if 'codes' in s)))
    data = compose(services, incidents, probes, heartbeat)
    dest = ROOT/'dist'
    dest.mkdir(exist_ok=True)
    for name in ('style.css', 'app.js', 'favicon.svg', '404.html'):
        shutil.copyfile(ROOT/'web'/name, dest/name)
    if (ROOT/'web'/'fonts').is_dir():
        shutil.copytree(ROOT/'web'/'fonts', dest/'fonts', dirs_exist_ok=True)
    (dest/'status.json').write_text(json.dumps(data, ensure_ascii=False, separators=(',',':')), encoding='utf-8')
    page = (ROOT/'web'/'index.html').read_text(encoding='utf-8')
    page = page.replace('<!--SERVICES-->', ''.join(service_html(item) for item in data['services']))
    page = page.replace('<!--INCIDENTS-->', incident_html(incidents))
    stamp = datetime.fromisoformat(data['generatedAt']).astimezone(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')
    page = page.replace('<!--UPDATED-->',f'<time datetime="{data["generatedAt"]}">{stamp}</time>')
    (dest/'index.html').write_text(page, encoding='utf-8')
    (dest/'CNAME').write_text('status.rexcorp.space\n', encoding='ascii')
    (dest/'.nojekyll').touch()
    (dest/'robots.txt').write_text('User-agent: *\nAllow: /\n', encoding='ascii')
    print(f'Built {len(data["services"])} public service statuses; active incidents: {sum(bool(i["active"]) for i in incidents)}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-probes', action='store_true')
    parser.add_argument('--heartbeat')
    args = parser.parse_args()
    build(not args.no_probes, args.heartbeat)
