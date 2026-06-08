const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

const initData = tg?.initData || "";
const headers = initData ? { "X-Telegram-Init-Data": initData } : {};
const subtitle = document.querySelector("#subtitle");
const chart = document.querySelector("#chart");
const birthData = document.querySelector("#birth-data");
const subscription = document.querySelector("#subscription");
const dialog = document.querySelector("#reading-dialog");
const readingText = document.querySelector("#reading-text");

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json();
}

async function loadProfile() {
  const profile = await request("/api/profile");
  subtitle.textContent = `Здравствуйте, ${profile.first_name || "звездный исследователь"}!`;
  subscription.textContent = `${profile.subscription_type} ${
    profile.subscription_expires_at ? `до ${new Date(profile.subscription_expires_at).toLocaleDateString("ru-RU")}` : ""
  }`;
  if (profile.birth_data) {
    birthData.textContent = `${profile.birth_data.birth_date}, ${profile.birth_data.birth_time || "12:00"}, ${
      profile.birth_data.birth_place
    }`;
  }
}

async function loadChart() {
  const payload = await request("/api/chart.svg");
  chart.innerHTML = payload.svg;
}

document.querySelector("#reading-button").addEventListener("click", async () => {
  readingText.textContent = "Готовлю интерпретацию...";
  dialog.showModal();
  try {
    const payload = await request("/api/reading", { method: "POST" });
    readingText.textContent = payload.reading;
  } catch (error) {
    readingText.textContent = `Не удалось получить чтение: ${error.message}`;
  }
});

document.querySelector("#upgrade-button").addEventListener("click", () => {
  tg?.close();
});

document.querySelector("#close-dialog").addEventListener("click", () => dialog.close());

Promise.all([loadProfile(), loadChart()]).catch((error) => {
  subtitle.textContent = "Откройте /start в боте и создайте натальную карту.";
  chart.textContent = error.message;
});
