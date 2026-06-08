'use strict';

const tg = window.Telegram?.WebApp;
const API_BASE = '';

let userId = null;
let userData = null;
let chartData = null;

// Init
document.addEventListener('DOMContentLoaded', async () => {
    if (tg) {
        tg.ready();
        tg.expand();
        tg.setHeaderColor('#0d0d1f');
        tg.setBackgroundColor('#0d0d1f');
    }

    userId = tg?.initDataUnsafe?.user?.id;

    if (!userId) {
        showError('Откройте приложение через Telegram бот');
        return;
    }

    setupTabs();
    await loadInitialData();
});

function setupTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`tab-${targetTab}`)?.classList.add('active');

            if (targetTab === 'chart' && !chartData) {
                loadChart();
            } else if (targetTab === 'profile') {
                loadProfile();
            }
        });
    });
}

async function loadInitialData() {
    try {
        userData = await fetchJSON(`/api/user/${userId}`);
        updateSubscriptionBadge();
        await loadChart();
    } catch (e) {
        showChartError('Данные рождения не найдены. Используйте /start в боте.');
    }
}

async function loadChart() {
    const container = document.getElementById('chartContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><div class="spinner"></div><p>Загружаю карту...</p></div>';

    try {
        const svgUrl = `${API_BASE}/api/chart/${userId}/svg`;
        const imgEl = document.createElement('img');
        imgEl.src = svgUrl;
        imgEl.alt = 'Натальная карта';
        imgEl.style.width = '100%';
        imgEl.style.height = '100%';
        imgEl.style.objectFit = 'contain';

        imgEl.onload = () => {
            container.innerHTML = '';
            container.appendChild(imgEl);
        };
        imgEl.onerror = () => {
            showChartError('Карта не найдена. Зарегистрируйтесь через /start');
        };

        chartData = await fetchJSON(`/api/chart/${userId}`);
        renderChartInfo(chartData);
    } catch (e) {
        showChartError('Ошибка загрузки карты');
    }
}

function renderChartInfo(data) {
    const infoEl = document.getElementById('chartInfo');
    if (!infoEl || !data?.planets) return;

    const signs = { ru: data.planets };
    const sun = data.planets?.Sun;
    const moon = data.planets?.Moon;
    const asc = data.planets?.Ascendant;

    infoEl.innerHTML = `
        <div class="chart-info-item">
            <span class="chart-info-label">☉ Солнце</span>
            <span class="chart-info-value">${sun?.sign_ru || '—'}</span>
        </div>
        <div class="chart-info-item">
            <span class="chart-info-label">☽ Луна</span>
            <span class="chart-info-value">${moon?.sign_ru || '—'}</span>
        </div>
        <div class="chart-info-item">
            <span class="chart-info-label">↑ Асц.</span>
            <span class="chart-info-value">${asc?.sign_ru || '—'}</span>
        </div>
    `;
}

function loadProfile() {
    const nameEl = document.getElementById('profileName');
    const subEl = document.getElementById('profileSub');
    const gridEl = document.getElementById('birthInfoGrid');

    if (userData && nameEl) {
        nameEl.textContent = userData.display_name || 'Пользователь';
        if (subEl) {
            const subNames = {
                'free': '🆓 Бесплатный план',
                'pro': '⭐ Stellarium Pro',
                'oracle': '🔮 Космический Оракул',
            };
            let subText = subNames[userData.subscription_type] || userData.subscription_type;
            if (userData.subscription_expires_at) {
                const exp = new Date(userData.subscription_expires_at);
                subText += ` · до ${exp.toLocaleDateString('ru-RU')}`;
            }
            subEl.textContent = subText;
        }
    }

    if (chartData && gridEl) {
        const bd = chartData.birth_date ? new Date(chartData.birth_date).toLocaleDateString('ru-RU') : '—';
        const bt = chartData.birth_time || 'Не указано';
        gridEl.innerHTML = `
            <div class="info-item">
                <span class="info-label">Дата рождения</span>
                <span class="info-value">${bd}</span>
            </div>
            <div class="info-item">
                <span class="info-label">Время</span>
                <span class="info-value">${bt}</span>
            </div>
            <div class="info-item">
                <span class="info-label">☉ Солнце</span>
                <span class="info-value">${chartData.planets?.Sun?.sign_ru || '—'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">☽ Луна</span>
                <span class="info-value">${chartData.planets?.Moon?.sign_ru || '—'}</span>
            </div>
        `;
    }
}

function updateSubscriptionBadge() {
    const badge = document.getElementById('subscriptionBadge');
    const label = document.getElementById('subLabel');
    if (!badge || !label || !userData) return;

    const sub = userData.subscription_type;
    if (sub === 'oracle') {
        label.textContent = '🔮 Оракул';
        badge.classList.add('pro');
    } else if (sub === 'pro') {
        label.textContent = '⭐ Pro';
        badge.classList.add('pro');
    } else {
        label.textContent = '🆓 Free';
    }
}

function openInBot(command) {
    if (tg) {
        tg.openTelegramLink(`https://t.me/stellarium_ai_bot?start=${command}`);
        tg.close();
    }
}

function showChartError(msg) {
    const container = document.getElementById('chartContainer');
    if (container) {
        container.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:20px;">${msg}</p>`;
    }
}

function showError(msg) {
    document.body.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;text-align:center;color:#9999cc;">
            <div>
                <div style="font-size:48px;margin-bottom:16px;">⚠️</div>
                <p>${msg}</p>
            </div>
        </div>
    `;
}

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}
