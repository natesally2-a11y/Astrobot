const userId = Number(window.STELLARIUM_USER_ID || 0);
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

function switchTab(tab) {
  document.querySelectorAll(".nav button").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });
  document.querySelectorAll(".tab").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `tab-${tab}`);
  });
}

document.querySelectorAll(".nav button").forEach((btn) => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});

async function fetchJson(url, options = {}) {
  const resp = await fetch(url, options);
  if (!resp.ok) {
    const payload = await resp.json().catch(() => ({}));
    throw new Error(payload.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function loadProfile() {
  const profile = await fetchJson(`/api/profile/${userId}`);
  const label = profile.username ? `@${profile.username}` : profile.first_name || "user";
  const exp = profile.subscription_expires_at || "не активна";
  document.getElementById("profile").textContent = `Профиль: ${label} · План: ${profile.subscription_type} · до ${exp}`;
}

async function loadChart() {
  const payload = await fetchJson(`/api/chart/${userId}`);
  document.getElementById("chart-svg").innerHTML = payload.svg;
}

async function loadTransits() {
  const payload = await fetchJson(`/api/transits/${userId}`);
  const list = payload.transits
    .slice(0, 10)
    .map((t) => `<li>${t.planet_a} — ${t.aspect_type} — ${t.planet_b} (orb ${t.orb}°)</li>`)
    .join("");
  document.getElementById("transits-result").innerHTML = `
    <p>${payload.analysis}</p>
    <ul>${list}</ul>
  `;
}

document.getElementById("compatibility-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = {
    user_id: userId,
    partner_birth_date: form.get("partner_birth_date"),
    partner_birth_time: form.get("partner_birth_time"),
    partner_place: form.get("partner_place"),
  };
  const resultNode = document.getElementById("compatibility-result");
  resultNode.textContent = "Рассчитываем...";
  try {
    const payload = await fetchJson("/api/compatibility", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    resultNode.innerHTML = `<h3>Совместимость: ${payload.score}/99</h3><p>${payload.report}</p>`;
  } catch (error) {
    resultNode.textContent = `Ошибка: ${error.message}`;
  }
});

async function bootstrap() {
  if (!userId) {
    document.getElementById("profile").textContent =
      "Не передан user_id. Откройте mini app из бота.";
    return;
  }
  try {
    await Promise.all([loadProfile(), loadChart(), loadTransits()]);
  } catch (error) {
    document.getElementById("profile").textContent = `Ошибка инициализации: ${error.message}`;
  }
}

bootstrap();
