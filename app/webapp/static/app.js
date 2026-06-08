/* Stellarium AI — клиент Mini App */
const tg = window.Telegram ? window.Telegram.WebApp : null;
if (tg) {
  tg.ready();
  tg.expand();
}

const initData = tg ? tg.initData : "";
let STATE = { isPremium: false };

function api(path, body) {
  return fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(Object.assign({ init_data: initData }, body || {})),
  }).then((r) => {
    if (!r.ok) return r.json().then((e) => Promise.reject(e));
    return r.json();
  });
}

/* Вкладки */
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
  });
});

function renderChart(data) {
  const wrap = document.getElementById("chart-wrap");
  if (!data.chart) {
    wrap.innerHTML = '<div class="loader">Натальная карта ещё не создана. Откройте чат с ботом и нажмите /start.</div>';
    return;
  }
  wrap.innerHTML = data.chart.svg;

  const meta = [];
  if (data.chart.ascendant) meta.push("Асцендент: " + data.chart.ascendant.sign);
  const sun = data.chart.planets.find((p) => p.key === "sun");
  const moon = data.chart.planets.find((p) => p.key === "moon");
  if (sun) meta.push("☉ " + sun.sign);
  if (moon) meta.push("☽ " + moon.sign);
  document.getElementById("chart-meta").textContent = meta.join(" · ");

  const pl = document.getElementById("planet-list");
  pl.innerHTML = data.chart.planets
    .map((p) => `<li><span><span class="sym">${p.symbol}</span>${p.name}</span>
      <span>${p.sign} ${p.degree.toFixed(1)}°${p.retrograde ? ' <span class="retro">R</span>' : ""}${p.house ? " · дом " + p.house : ""}</span></li>`)
    .join("");

  const al = document.getElementById("aspect-list");
  al.innerHTML = data.chart.aspects
    .map((a) => `<li><span>${a.body1} ${a.symbol} ${a.body2}</span><span>${a.name} (${a.orb}°)</span></li>`)
    .join("") || "<li>Значимых аспектов не найдено</li>";
}

function renderProfile(data) {
  const badge = document.getElementById("subscription");
  badge.textContent = data.subscription ? data.subscription.title : "Free";
  STATE.isPremium = data.subscription && data.subscription.is_premium && data.subscription.active;

  const prof = document.getElementById("profile");
  const sub = data.subscription || {};
  let exp = sub.expires_at ? new Date(sub.expires_at).toLocaleDateString("ru-RU") : "—";
  prof.innerHTML = `
    <div>Имя: <b>${data.first_name || "—"}</b></div>
    <div>Тариф: <b>${sub.title || "Free"}</b></div>
    <div>Активна до: <b>${sub.active ? exp : "—"}</b></div>
    <div>Приглашено друзей: <b>${data.referral_count || 0}</b></div>
    ${data.birth ? `<div>Рождение: <b>${data.birth.date} ${data.birth.time || ""}</b></div><div>Место: <b>${data.birth.place}</b></div>` : ""}
  `;

  const locked = document.getElementById("transits-locked");
  const loadBtn = document.getElementById("load-transits");
  if (STATE.isPremium) {
    locked.classList.add("hidden");
    loadBtn.classList.remove("hidden");
  } else {
    locked.classList.remove("hidden");
    loadBtn.classList.add("hidden");
  }
}

function closeToChat() {
  if (tg) tg.close();
}

document.getElementById("get-reading").addEventListener("click", closeToChat);
document.getElementById("upgrade").addEventListener("click", closeToChat);
document.getElementById("upgrade-from-transits").addEventListener("click", closeToChat);

document.getElementById("c-submit").addEventListener("click", () => {
  const res = document.getElementById("c-result");
  const date = document.getElementById("c-date").value;
  const city = document.getElementById("c-city").value;
  if (!date || !city) {
    res.textContent = "Укажите дату и город рождения партнёра.";
    return;
  }
  res.textContent = "Сравниваю карты…";
  api("/api/compatibility", {
    partner_name: document.getElementById("c-name").value || "Партнёр",
    birth_date: date,
    birth_time: document.getElementById("c-time").value || null,
    city: city,
  })
    .then((d) => { res.textContent = d.interpretation; })
    .catch((e) => { res.textContent = "Ошибка: " + (e.detail || "не удалось рассчитать"); });
});

document.getElementById("load-transits").addEventListener("click", () => {
  const res = document.getElementById("transits-result");
  res.textContent = "Считаю транзиты…";
  api("/api/transits", {})
    .then((d) => { res.textContent = d.interpretation; })
    .catch((e) => { res.textContent = "Ошибка: " + (e.detail || "недоступно"); });
});

/* Инициализация */
api("/api/me", {})
  .then((data) => {
    if (!data.registered) {
      document.getElementById("chart-wrap").innerHTML =
        '<div class="loader">Профиль не найден. Откройте чат с ботом и нажмите /start.</div>';
      return;
    }
    renderChart(data);
    renderProfile(data);
  })
  .catch((e) => {
    document.getElementById("chart-wrap").innerHTML =
      '<div class="loader">Не удалось авторизоваться: ' + (e.detail || "ошибка") + "</div>";
  });
