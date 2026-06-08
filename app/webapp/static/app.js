const body = document.body;
const baseUrl = body.dataset.baseUrl || "";

function resolveTelegramId() {
  const explicit = body.dataset.telegramId;
  if (explicit) return explicit;

  const tg = window.Telegram?.WebApp;
  tg?.ready();
  tg?.expand();
  return tg?.initDataUnsafe?.user?.id || "";
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return response.json();
}

function renderReadings(readings) {
  const list = document.getElementById("reading-list");
  list.innerHTML = "";
  if (!readings?.length) {
    const item = document.createElement("li");
    item.textContent = "История чтений появится после первых запросов в боте.";
    list.appendChild(item);
    return;
  }

  readings.forEach((reading) => {
    const item = document.createElement("li");
    item.innerHTML = `<strong>${reading.reading_type}</strong><br />${reading.excerpt}`;
    list.appendChild(item);
  });
}

async function bootstrap() {
  const telegramId = resolveTelegramId();
  const suffix = telegramId ? `?telegram_id=${telegramId}` : "";

  const [profile, daily] = await Promise.all([
    fetchJson(`${baseUrl}/api/webapp/profile${suffix}`),
    fetchJson(`${baseUrl}/api/webapp/daily${suffix}`),
  ]);

  document.getElementById("plan-pill").textContent = profile.plan;
  document.getElementById("chart-summary").textContent = profile.chart_summary;
  document.getElementById("daily-forecast").textContent = daily.forecast;
  renderReadings(profile.recent_readings);
  document.getElementById("chart-image").src = `${baseUrl}/api/webapp/chart.svg${suffix}`;

  document.getElementById("open-chat").addEventListener("click", () => {
    const botUsername = window.Telegram?.WebApp?.initDataUnsafe?.receiver?.username;
    if (botUsername) {
      window.open(`https://t.me/${botUsername}`, "_blank");
      return;
    }
    window.location.href = "https://t.me/";
  });
}

bootstrap().catch((error) => {
  document.getElementById("chart-summary").textContent =
    "Не удалось загрузить данные mini app. Проверьте API и конфигурацию.";
  console.error(error);
});
