const tg = window.Telegram?.WebApp;
tg?.ready();
tg?.expand();

const params = new URLSearchParams(window.location.search);
const devUserId = params.get("telegram_id") || params.get("tg_user");
const initData = tg?.initData || "";

function authQuery() {
  const query = new URLSearchParams();
  if (initData) {
    query.set("initData", initData);
  } else if (devUserId) {
    query.set("telegram_id", devUserId);
  }
  return query.toString();
}

async function api(path, options = {}) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(`${path}${separator}${authQuery()}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

async function loadProfile() {
  try {
    const profile = await api("/api/me");
    setText(
      "profile",
      `Тариф: ${profile.subscription_type}. Карта создана: ${profile.has_birth_data ? "да" : "нет"}. GDPR/152-ФЗ: ${
        profile.gdpr_consent ? "согласие есть" : "нет согласия"
      }.`
    );
  } catch (error) {
    setText("profile", `Профиль не найден: ${error.message}. Откройте бота и пройдите /start.`);
  }
}

async function loadChart() {
  try {
    const chart = await api("/api/chart");
    document.getElementById("chart").innerHTML = chart.svg;
    document.getElementById("planetTable").innerHTML = chart.planets
      .map(
        (planet) =>
          `<div class="planet"><strong>${planet.label}</strong><br>${planet.sign} ${planet.degree}°<br>Дом: ${
            planet.house || "не рассчитан"
          }</div>`
      )
      .join("");
    document.getElementById("transits").innerHTML = chart.transits.length
      ? chart.transits
          .map((item) => `• ${item.transit_planet} ${item.aspect} ${item.natal_planet}, орб ${item.orb}°`)
          .join("<br>")
      : "На сегодня нет точных сильных транзитов.";
  } catch (error) {
    document.getElementById("chart").textContent = `Карта недоступна: ${error.message}`;
    setText("transits", "Транзиты появятся после создания карты.");
  }
}

async function loadReadings() {
  try {
    const readings = await api("/api/readings");
    document.getElementById("readings").innerHTML =
      readings
        .map(
          (reading) =>
            `<div class="reading-item"><strong>${reading.type}</strong><br>${reading.response.slice(0, 360)}${
              reading.response.length > 360 ? "..." : ""
            }</div>`
        )
        .join("") || "История пока пуста.";
  } catch (error) {
    setText("readings", `История недоступна: ${error.message}`);
  }
}

document.getElementById("refreshChart").addEventListener("click", loadChart);

document.getElementById("openBot").addEventListener("click", () => {
  const username = window.STELLARIUM_BOT_USERNAME || "stellarium_ai_bot";
  tg?.openTelegramLink(`https://t.me/${username}`);
});

document.getElementById("compatibilityForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const payload = Object.fromEntries(form.entries());
  try {
    setText("compatibilityResult", "Считаю совместимость...");
    const result = await api("/api/compatibility", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setText("compatibilityResult", result.reading);
    await loadReadings();
  } catch (error) {
    setText("compatibilityResult", `Ошибка: ${error.message}`);
  }
});

loadProfile();
loadChart();
loadReadings();
