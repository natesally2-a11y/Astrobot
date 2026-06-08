const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const PLAN_LABELS = { free: 'Free', pro: 'Pro', oracle: 'Оракул' };

function getInitData() {
    return tg.initData || '';
}

async function apiFetch(path) {
    const res = await fetch(path, {
        headers: { 'X-Telegram-Init-Data': getInitData() },
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.message || err.detail || 'Ошибка загрузки');
    }
    return res.json();
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === tabName));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === `tab-${tabName}`));
    if (tabName === 'readings') loadReadings();
    if (tabName === 'settings') loadProfile();
}

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
});

async function loadChart() {
    const container = document.getElementById('chart-container');
    const info = document.getElementById('chart-info');
    try {
        const data = await apiFetch('/app/chart');
        container.innerHTML = data.chart.svg;
        document.getElementById('plan-badge').textContent = PLAN_LABELS[data.subscription] || data.subscription;

        const planets = data.chart.planets.map(p =>
            `<div class="planet-item">${p.sign_emoji} ${p.name}: ${p.sign} ${p.degree}°</div>`
        ).join('');
        info.innerHTML = `
            <strong>📍 ${data.birth_place}</strong><br>
            📅 ${data.birth_date}<br>
            ASC: ${data.chart.ascendant_sign}
            <div class="planet-list">${planets}</div>
        `;

        const upgradeBtn = document.getElementById('btn-upgrade');
        if (data.subscription === 'free') {
            upgradeBtn.classList.remove('hidden');
        } else {
            upgradeBtn.classList.add('hidden');
        }
    } catch (e) {
        container.innerHTML = `<div class="error">${e.message}<br><br>Используйте /start в боте для создания карты.</div>`;
        info.innerHTML = '';
    }
}

async function loadReadings() {
    const list = document.getElementById('readings-list');
    try {
        const data = await apiFetch('/app/readings');
        if (!data.readings.length) {
            list.innerHTML = '<div class="empty">Пока нет чтений. Спросите астролога в чате!</div>';
            return;
        }
        list.innerHTML = data.readings.map(r => `
            <div class="reading-card">
                <div class="type">${r.type}</div>
                ${r.question ? `<div><em>${r.question}</em></div>` : ''}
                <div>${r.response || ''}</div>
                <div class="date">${r.created_at ? new Date(r.created_at).toLocaleString('ru') : ''}</div>
            </div>
        `).join('');
    } catch (e) {
        list.innerHTML = `<div class="error">${e.message}</div>`;
    }
}

async function loadProfile() {
    const el = document.getElementById('profile-info');
    try {
        const data = await apiFetch('/app/profile');
        el.innerHTML = `
            <p>👤 ${data.first_name || 'Пользователь'}</p>
            <p>💎 Тариф: ${PLAN_LABELS[data.subscription] || data.subscription}</p>
            <p>📊 Карта: ${data.has_chart ? '✅ создана' : '❌ нет'}</p>
            ${data.subscription_expires ? `<p>📅 До: ${new Date(data.subscription_expires).toLocaleDateString('ru')}</p>` : ''}
        `;
    } catch (e) {
        el.innerHTML = `<div class="error">${e.message}</div>`;
    }
}

document.getElementById('btn-reading').addEventListener('click', () => {
    tg.close();
});

document.getElementById('btn-upgrade').addEventListener('click', () => {
    switchTab('settings');
});

document.getElementById('btn-subscribe-pro').addEventListener('click', () => {
    tg.close();
});

document.getElementById('btn-subscribe-oracle').addEventListener('click', () => {
    tg.close();
});

loadChart();
