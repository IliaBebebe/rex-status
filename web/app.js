'use strict';
(() => {
  const list = document.querySelector('#service-list');
  const refresh = document.querySelector('#refresh');
  const notice = document.querySelector('#data-notice');
  const labels = {operational:'Работает', limited:'Доступ ограничен', outage:'Не отвечает', unknown:'Нет свежих данных'};
  let snapshot = null;
  let filter = 'all';
  let busy = false;
  function applyFilter() {
    for (const row of list.children) row.hidden = filter !== 'all' && row.dataset.group !== filter;
  }
  document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
    filter = button.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    applyFilter();
  }));
  function old(timestamp, minutes) {
    const elapsed = Date.now() - Date.parse(timestamp);
    return !Number.isFinite(elapsed) || elapsed < -60000 || elapsed > minutes * 60000;
  }
  function render(data) {
    if (!Array.isArray(data.services)) throw new Error('Invalid status data');
    snapshot = data;
    const stale = old(data.generatedAt, 45);
    const rows = new Map([...list.children].map(row => [row.querySelector('h3').textContent.replace(' (откроется в новой вкладке)', ''), row]));
    let outages = 0;
    let unknown = 0;
    let limited = 0;
    for (const service of data.services) {
      const row = rows.get(service.name);
      if (!row) continue;
      const expired = stale || (service.group === 'telegram' && old(service.checkedAt, 35));
      const state = expired ? 'unknown' : Object.hasOwn(labels, service.status) ? service.status : 'unknown';
      const pill = row.querySelector('.pill');
      pill.className = 'pill ' + state;
      pill.replaceChildren(Object.assign(document.createElement('span'), {className:'dot'}), document.createTextNode(labels[state]));
      pill.firstChild.setAttribute('aria-hidden', 'true');
      row.dataset.status = state;
      row.querySelector('.service-note').textContent = expired ? 'Последняя проверка устарела' : service.note;
      if (state === 'outage') outages++;
      if (state === 'unknown') unknown++;
      if (state === 'limited') limited++;
    }
    const time = document.createElement('time');
    time.dateTime = data.generatedAt;
    time.textContent = new Intl.DateTimeFormat('ru-RU', {day:'numeric',month:'long',hour:'2-digit',minute:'2-digit',timeZone:'Europe/Moscow'}).format(new Date(data.generatedAt)) + ' МСК';
    document.querySelector('#updated').replaceChildren(document.createTextNode('Обновлено: '), time);
    const active = data.incidents.some(incident => incident.active);
    const overview = document.querySelector('.overview');
    overview.className = 'overview' + (stale ? ' is-unknown' : outages ? ' is-outage' : !active && !unknown && !limited ? ' is-operational' : '');
    document.querySelector('#overall-title').textContent = stale ? 'Нет свежей сводки' : outages ? 'Есть недоступные сервисы' : active || limited ? 'Есть ограничения доступа' : unknown ? 'Не все проверки получены' : 'Сервисы отвечают';
    document.querySelector('#overall-description').textContent = stale ? 'Показаны последние сохранённые данные. Известная проблема доступа остаётся открытой.' : active ? 'Некоторые сайты могут не открываться без VPN.' : unknown ? 'Для части сервисов ожидаем новую проверку.' : 'По последним проверкам открытых ограничений нет.';
    notice.hidden = !stale;
    if (stale) notice.textContent = 'Сводка не обновлялась больше 45 минут. Состояние сервисов сейчас не подтверждено. Сохранённые сообщения о сбоях доступны ниже.';
    applyFilter();
  }
  async function update(manual = false) {
    if (busy) return;
    busy = true;
    refresh.disabled = true;
    refresh.textContent = 'Проверяем сводку…';
    try {
      const response = await fetch('./status.json?t=' + Math.floor(Date.now() / 60000), {cache:'no-store', signal:AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error('Status unavailable');
      render(await response.json());
    } catch {
      notice.hidden = false;
      notice.textContent = 'Не удалось загрузить новую сводку. Показаны последние сохранённые данные. Попробуйте обновить страницу позже.';
    } finally {
      busy = false;
      refresh.disabled = false;
      refresh.textContent = 'Обновить данные';
    }
  }
  refresh.hidden = false;
  refresh.addEventListener('click', () => update(true));
  const initial = document.querySelector('#updated time');
  if (initial && old(initial.dateTime, 45)) {
    notice.hidden = false;
    notice.textContent = 'Сохранённая сводка устарела. Загружаем более свежие данные.';
    for (const row of list.children) {
      row.dataset.status = 'unknown';
      row.querySelector('.pill').className = 'pill unknown';
      row.querySelector('.pill').textContent = labels.unknown;
    }
  }
  update();
  setInterval(() => {
    if (snapshot) render(snapshot);
    if (!document.hidden) update();
  }, 60000);
})();
