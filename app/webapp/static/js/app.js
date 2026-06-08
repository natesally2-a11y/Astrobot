/* Stellarium AI — Mini App front-end */
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
    tg.ready();
    tg.expand();
}

const INIT_DATA = tg ? tg.initData : "";

async function api(path, options = {}) {
    const headers = Object.assign(
        { "X-Telegram-Init-Data": INIT_DATA, "Content-Type": "application/json" },
        options.headers || {}
    );
    const res = await fetch(`/api${path}`, { ...options, headers });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Ошибка запроса");
    }
    return res.json();
}

/* ---- Tabs ---- */
document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        const name = btn.dataset.tab;
        document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById(`tab-${name}`).classList.add("active");
        if (name === "transits") loadTransits();
    });
});

/* ---- Profile ---- */
async function loadProfile() {
    try {
        const me = await api("/me");
        document.getElementById("plan-badge").textContent = me.subscription_title || "Free";
        const info = document.getElementById("profile-info");
        if (!me.registered) {
            info.innerHTML = "Откройте бота и создайте натальную карту командой /start.";
            return;
        }
        const expires = me.subscription_expires_at
            ? new Date(me.subscription_expires_at).toLocaleDateString("ru-RU")
            : "—";
        const q = me.remaining_questions === -1 ? "безлимит" : me.remaining_questions;
        info.innerHTML = `
            <div>👤 <b>${me.first_name || "Пользователь"}</b></div>
            <div>Тариф: <b>${me.subscription_title}</b></div>
            <div>Действует до: ${expires}</div>
            <div>Вопросов сегодня: ${q}</div>
            <div>Приглашено друзей: ${me.referral_count}</div>`;
    } catch (e) {
        document.getElementById("plan-badge").textContent = "—";
    }
}

/* ---- Chart ---- */
async function loadChart() {
    const wrap = document.getElementById("chart-wrap");
    const meta = document.getElementById("chart-meta");
    const list = document.getElementById("planets-list");
    try {
        const data = await api("/chart");
        wrap.innerHTML = data.svg;
        const asc = data.ascendant ? `, Асцендент ${data.ascendant.sign}` : "";
        meta.textContent = `${data.birth.place} · ${data.birth.date}${asc}`;
        list.innerHTML = data.planets
            .map(
                (p) => `<div class="row">
                    <span class="name">${p.name}</span>
                    <span>${p.position}${p.house ? " · дом " + p.house : ""}
                    ${p.retrograde ? '<span class="retro">R</span>' : ""}</span>
                </div>`
            )
            .join("");
    } catch (e) {
        wrap.innerHTML = `<div class="loader">${e.message}</div>`;
    }
}

/* ---- Transits ---- */
let transitsLoaded = false;
async function loadTransits() {
    if (transitsLoaded) return;
    const box = document.getElementById("transits-result");
    try {
        const data = await api("/transits");
        if (!data.is_premium) {
            box.innerHTML =
                '<div class="card">🔒 Подробные транзиты доступны по подписке Premium. Оформите её во вкладке «Профиль».</div>';
        }
        const rows = data.transits
            .map(
                (t) => `<div class="row"><span class="name">${t.transiting} → ${t.natal}</span>
                <span>${t.type} (${t.orb}°)</span></div>`
            )
            .join("");
        box.innerHTML += rows || '<div class="card">Значимых транзитов сейчас нет.</div>';
        transitsLoaded = true;
    } catch (e) {
        box.innerHTML = `<div class="card">${e.message}</div>`;
    }
}

/* ---- Compatibility ---- */
document.getElementById("calc-compat").addEventListener("click", async () => {
    const box = document.getElementById("compat-result");
    box.innerHTML = '<div class="loader">Рассчитываю…</div>';
    const body = {
        date: document.getElementById("p-date").value,
        time: document.getElementById("p-time").value || null,
        place: document.getElementById("p-place").value || null,
    };
    if (!body.date) {
        box.innerHTML = '<div class="card">Укажите дату рождения партнёра.</div>';
        return;
    }
    try {
        const data = await api("/compatibility", { method: "POST", body: JSON.stringify(body) });
        box.innerHTML = `
            <div class="score">${data.score}%</div>
            <div class="card">${data.hint}</div>`;
    } catch (e) {
        box.innerHTML = `<div class="card">${e.message}</div>`;
    }
});

/* ---- Actions ---- */
document.getElementById("open-bot-reading").addEventListener("click", () => {
    if (tg) {
        tg.close();
    }
});
document.getElementById("upgrade-btn").addEventListener("click", () => {
    if (tg) tg.close();
});
document.getElementById("link-privacy").addEventListener("click", (e) => {
    e.preventDefault();
    if (tg) tg.openTelegramLink(`https://t.me/share`);
});

/* ---- Init ---- */
loadProfile();
loadChart();
