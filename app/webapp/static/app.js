const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const state = {
  telegramId: tg?.initDataUnsafe?.user?.id || window.STELLARIUM_APP.defaultTelegramId,
  botUsername: window.STELLARIUM_APP.botUsername,
};

const profileEl = document.getElementById('profile');
const subscriptionEl = document.getElementById('subscription');
const chartWrapperEl = document.getElementById('chart-wrapper');
const readingsEl = document.getElementById('readings');
const heroTextEl = document.getElementById('hero-text');
const compatibilityForm = document.getElementById('compatibility-form');
const compatibilityResult = document.getElementById('compatibility-result');

document.getElementById('open-bot').addEventListener('click', () => {
  if (state.botUsername) {
    window.open(`https://t.me/${state.botUsername}`);
  }
});
document.getElementById('refresh-data').addEventListener('click', () => loadAll());

function renderList(items, emptyText) {
  if (!items.length) {
    return `<p class="muted">${emptyText}</p>`;
  }
  return `<div class="list">${items.map(item => `<div class="list-item">${item}</div>`).join('')}</div>`;
}

async function fetchJson(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

async function loadAll() {
  if (!state.telegramId) {
    heroTextEl.textContent = 'Telegram ID не найден. Откройте Mini App из бота или добавьте ?telegram_id=777000 для демо.';
    return;
  }
  heroTextEl.textContent = `Загружаем профиль #${state.telegramId}...`;
  try {
    const [profile, chart, readings] = await Promise.all([
      fetchJson(`/api/users/${state.telegramId}`),
      fetchJson(`/api/chart/${state.telegramId}`),
      fetchJson(`/api/readings/${state.telegramId}`),
    ]);
    heroTextEl.textContent = 'Профиль загружен. Карта и история готовы.';
    profileEl.innerHTML = `
      <p><strong>${profile.first_name || 'Без имени'}</strong></p>
      <p class="muted">Telegram ID: ${profile.telegram_id}</p>
      <p class="muted">GDPR consent: ${profile.gdpr_consent ? 'yes' : 'no'}</p>
    `;
    subscriptionEl.innerHTML = `
      <p><strong>${profile.subscription_type}</strong></p>
      <p class="muted">До: ${profile.subscription_expires_at || '—'}</p>
    `;
    chartWrapperEl.innerHTML = chart.svg;
    readingsEl.innerHTML = renderList(
      readings.map(item => `<strong>${item.reading_type}</strong><br/><span class="muted">${new Date(item.created_at).toLocaleString()}</span><br/>${item.ai_response}`),
      'Пока нет сохраненных чтений.'
    );
  } catch (error) {
    heroTextEl.textContent = 'Не удалось загрузить данные. Проверьте, что профиль создан в боте и demo data включены.';
    profileEl.innerHTML = `<p class="muted">${error.message}</p>`;
    subscriptionEl.innerHTML = '<p class="muted">—</p>';
    chartWrapperEl.innerHTML = '';
    readingsEl.innerHTML = '';
  }
}

compatibilityForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  compatibilityResult.textContent = 'Считаем совместимость...';
  const formData = new FormData(compatibilityForm);
  const payload = {
    telegram_id: state.telegramId,
    partner_name: formData.get('partner_name'),
    birth_date: formData.get('birth_date'),
    birth_time: formData.get('birth_time') || null,
    birth_place: formData.get('birth_place'),
    is_time_approximate: Boolean(formData.get('is_time_approximate')),
  };
  try {
    const result = await fetchJson('/api/compatibility', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    compatibilityResult.textContent = `${result.interpretation}

Score: ${result.report.score}/99
Partner place: ${result.partner_place}`;
  } catch (error) {
    compatibilityResult.textContent = `Ошибка: ${error.message}`;
  }
});

loadAll();
