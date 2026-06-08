const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_BASE = '/api';
let currentUserId = null;
let userData = null;

function init() {
    if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
        currentUserId = tg.initDataUnsafe.user.id;
        const name = tg.initDataUnsafe.user.first_name || '';
        document.getElementById('userInfo').textContent = name;
    }

    setupTabs();

    if (currentUserId) {
        loadUserData();
        loadChart();
        loadPlans();
        loadReadings();
    }
}

function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
        });
    });
}

async function loadUserData() {
    try {
        const resp = await fetch(`${API_BASE}/user/${currentUserId}`);
        if (!resp.ok) return;
        userData = await resp.json();
        renderProfile();
        renderSubscription();

        if (userData.subscription !== 'free') {
            document.getElementById('premiumGate').classList.add('hidden');
            document.getElementById('transitsContent').classList.remove('hidden');
            document.getElementById('transitsContent').innerHTML =
                '<p>Перейдите в чат с ботом для анализа транзитов:</p>' +
                '<button class="btn btn-primary" onclick="openBot(\'/transit\')">Анализ транзитов</button>';
        }
    } catch (e) {
        console.error('Failed to load user data:', e);
    }
}

async function loadChart() {
    try {
        const resp = await fetch(`${API_BASE}/chart/${currentUserId}`);
        if (!resp.ok) {
            document.getElementById('chartContainer').innerHTML =
                '<p style="text-align:center;color:var(--text-secondary)">Нет данных рождения.<br>Используйте /start в боте.</p>';
            return;
        }
        const data = await resp.json();

        const svgResp = await fetch(`${API_BASE}/chart/${currentUserId}/svg`);
        if (svgResp.ok) {
            const svgText = await svgResp.text();
            document.getElementById('chartContainer').innerHTML = svgText;
        }

        renderChartSummary(data);
        renderPlanets(data.planets);
        renderAspects(data.aspects);
    } catch (e) {
        console.error('Failed to load chart:', e);
        document.getElementById('chartContainer').innerHTML = '<p>Ошибка загрузки</p>';
    }
}

function renderChartSummary(data) {
    const el = document.getElementById('chartSummary');
    el.innerHTML = `
        <div class="sign-item">
            <span class="sign-label">☀️ Солнце</span>
            <span class="sign-value">${data.sun_sign}</span>
        </div>
        <div class="sign-item">
            <span class="sign-label">🌙 Луна</span>
            <span class="sign-value">${data.moon_sign}</span>
        </div>
        <div class="sign-item">
            <span class="sign-label">⬆️ Асцендент</span>
            <span class="sign-value">${data.rising_sign}</span>
        </div>
    `;
}

function renderPlanets(planets) {
    const el = document.getElementById('planetsList');
    el.innerHTML = planets.map(p => `
        <div class="planet-row">
            <span class="symbol">${p.symbol}</span>
            <span class="name">${p.name}</span>
            <span class="position">${p.sign_symbol} ${p.sign} ${Math.floor(p.degree)}°</span>
            <span class="house">Дом ${p.house}</span>
            ${p.retrograde ? '<span class="retrograde">℞</span>' : ''}
        </div>
    `).join('');
}

function renderAspects(aspects) {
    const el = document.getElementById('aspectsList');
    const typeMap = {
        'Соединение': 'conjunction',
        'Секстиль': 'sextile',
        'Квадрат': 'square',
        'Тригон': 'trine',
        'Оппозиция': 'opposition',
    };
    el.innerHTML = aspects.slice(0, 15).map(a => `
        <div class="aspect-row">
            <span>${a.planet1}</span>
            <span class="type aspect-${typeMap[a.type] || ''}">${a.type}</span>
            <span>${a.planet2}</span>
            <span style="color:var(--text-secondary);font-size:11px">${a.orb}°</span>
        </div>
    `).join('');
}

function renderProfile() {
    if (!userData) return;
    const el = document.getElementById('profileInfo');
    let html = `<span class="label">Имя:</span> ${userData.first_name || '—'}<br>`;
    if (userData.birth_data) {
        html += `<span class="label">Дата рождения:</span> ${userData.birth_data.birth_date}<br>`;
        if (userData.birth_data.birth_time) {
            html += `<span class="label">Время:</span> ${userData.birth_data.birth_time}<br>`;
        }
        html += `<span class="label">Место:</span> ${userData.birth_data.birth_place}<br>`;
    }
    el.innerHTML = html;
}

function renderSubscription() {
    if (!userData) return;
    const names = { free: 'Бесплатный', pro: 'Stellarium Pro ⭐', oracle: 'Космический Оракул 🔮' };
    document.getElementById('subscriptionInfo').innerHTML =
        `<p>Текущий план: <strong>${names[userData.subscription] || userData.subscription}</strong></p>`;
}

async function loadPlans() {
    try {
        const resp = await fetch(`${API_BASE}/subscription/plans`);
        if (!resp.ok) return;
        const data = await resp.json();
        const el = document.getElementById('plansList');
        el.innerHTML = data.plans.map(p => `
            <div class="plan-card ${userData && userData.subscription === p.id ? 'active' : ''}">
                <div class="plan-name">${p.name}</div>
                <div class="plan-price">${p.price > 0 ? p.price + '₽/мес (' + p.stars + ' ⭐)' : 'Бесплатно'}</div>
                <ul class="plan-features">
                    ${p.features.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load plans:', e);
    }
}

async function loadReadings() {
    try {
        const resp = await fetch(`${API_BASE}/readings/${currentUserId}`);
        if (!resp.ok) return;
        const readings = await resp.json();
        const el = document.getElementById('readingsList');
        if (readings.length === 0) {
            el.innerHTML = '<p style="color:var(--text-secondary)">Нет истории чтений</p>';
            return;
        }
        const typeNames = { natal: 'Натальная', daily: 'Дневной', weekly: 'Недельный', compatibility: 'Совместимость', ask: 'Вопрос', transit: 'Транзиты' };
        el.innerHTML = readings.map(r => `
            <div class="reading-item">
                <span class="reading-type">${typeNames[r.type] || r.type}</span>
                <span class="reading-date">${r.date ? new Date(r.date).toLocaleDateString('ru') : ''}</span>
                <p style="margin-top:4px">${r.response || ''}</p>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to load readings:', e);
    }
}

function openBot(command) {
    if (tg.close) {
        tg.sendData(JSON.stringify({ action: 'command', command: command }));
    }
}

document.addEventListener('DOMContentLoaded', init);
