"""Public status model: never infer regional availability from one HTTP probe."""
from datetime import datetime, timezone

LABELS = {"operational":"Работает", "limited":"Доступ ограничен", "outage":"Не отвечает", "unknown":"Нет свежих данных"}
GROUPS = {"web":"Сайты и приложения", "identity":"Вход и панели", "telegram":"Telegram"}

def fresh(timestamp, now, minutes=35):
    try:
        date = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return 0 <= (now - date).total_seconds() <= minutes * 60
    except (ValueError, TypeError, AttributeError):
        return False

def compose(services, incidents, probes, heartbeat=None, now=None):
    now = now or datetime.now(timezone.utc)
    heartbeat = heartbeat or {}
    home_fresh = fresh(heartbeat.get("checkedAt"), now)
    home = heartbeat.get("services", {}) if home_fresh else {}
    active = [i for i in incidents if i.get("active")]
    affected = {group for incident in active for group in incident["affectedGroups"]}
    result = []
    for service in services:
        item = {k:service[k] for k in ("id", "name", "description", "url", "group") if k in service}
        local = home.get(service["id"])
        if service["group"] == "telegram":
            status = local if local in ("operational", "outage") else "unknown"
            note = "Подключение к Telegram подтверждено" if status == "operational" else "Не удалось подтвердить подключение" if status == "outage" else "Ожидаем новую проверку подключения"
            checked = heartbeat.get("checkedAt") if home_fresh else None
        else:
            probe = probes.get(service["id"], {})
            checked = probe.get("checkedAt")
            if not fresh(checked, now):
                status, note = "unknown", "Ожидаем новую проверку сайта"
            elif not probe.get("ok") or local == "outage":
                status, note = "outage", "Проверка не получила ожидаемый ответ"
            elif service["group"] in affected:
                status, note = "limited", "Сайт отвечает, но может не открываться без VPN"
            else:
                status, note = "operational", "Страница отвечает на внешнюю проверку"
        item.update(status=status, label=LABELS[status], note=note, checkedAt=checked)
        result.append(item)
    return {"schemaVersion":1, "generatedAt":now.isoformat(), "homeCheckedAt":heartbeat.get("checkedAt") if home_fresh else None, "services":result, "incidents":incidents, "groups":GROUPS}
