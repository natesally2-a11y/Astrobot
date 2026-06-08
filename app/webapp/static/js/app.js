/* Stellarium AI — Mini App front-end. */
(function () {
  const tg = window.Telegram && window.Telegram.WebApp;
  if (tg) {
    tg.ready();
    tg.expand();
  }

  const initData = (tg && tg.initData) || "";
  const headers = { "X-Telegram-Init-Data": initData };

  const statusEl = document.getElementById("status");
  const chartEl = document.getElementById("chartContainer");
  const summaryEl = document.getElementById("summary");
  const planetsBody = document.querySelector("#planetsTable tbody");
  const aspectsList = document.getElementById("aspectsList");
  const upgradeBtn = document.getElementById("upgradeBtn");
  const readingBtn = document.getElementById("readingBtn");

  function setStatus(text, premium) {
    statusEl.textContent = text;
    statusEl.classList.toggle("premium", !!premium);
  }

  async function jget(url) {
    const r = await fetch(url, { headers });
    if (!r.ok) throw new Error(`${r.status}`);
    return r.json();
  }

  function fmtDeg(d) {
    const deg = Math.floor(d);
    const min = Math.floor((d - deg) * 60);
    return `${deg}°${String(min).padStart(2, "0")}'`;
  }

  function renderSummary(chart) {
    summaryEl.innerHTML = `
      <div><strong>Солнце</strong>${chart.sun}</div>
      <div><strong>Луна</strong>${chart.moon}</div>
      <div><strong>Асцендент</strong>${chart.ascendant || "—"}</div>
    `;
  }

  function renderPlanets(chart) {
    planetsBody.innerHTML = chart.planets.map((p) => `
      <tr>
        <td>${p.glyph} ${p.name_ru}${p.retrograde ? " ℞" : ""}</td>
        <td>${p.sign_glyph} ${p.sign}</td>
        <td>${fmtDeg(p.sign_degree)}</td>
        <td>${p.house ?? "—"}</td>
      </tr>
    `).join("");
  }

  function renderAspects(chart) {
    if (!chart.aspects.length) {
      aspectsList.innerHTML = "<li>Аспекты не найдены</li>";
      return;
    }
    const byName = Object.fromEntries(chart.planets.map((p) => [p.name, p]));
    aspectsList.innerHTML = chart.aspects.slice(0, 12).map((a) => {
      const pa = byName[a.planet_a], pb = byName[a.planet_b];
      const cls = `aspect-${a.name}`;
      return `<li>
        <span>${pa.glyph} ${pa.name_ru} <span class="${cls}">${a.name_ru}</span> ${pb.glyph} ${pb.name_ru}</span>
        <span class="aspect-orb">орб ${a.orb.toFixed(1)}°</span>
      </li>`;
    }).join("");
  }

  async function loadChartSvg() {
    try {
      const r = await fetch("/api/chart.svg", { headers });
      if (!r.ok) throw new Error(`${r.status}`);
      const svg = await r.text();
      chartEl.innerHTML = svg;
    } catch (e) {
      chartEl.innerHTML = `<div class="error">Не удалось загрузить карту: ${e.message}</div>`;
    }
  }

  async function loadAll() {
    try {
      const me = await jget("/api/me");
      setStatus(
        me.is_premium ? `⭐ ${me.subscription_type.toUpperCase()}` : "Free",
        me.is_premium,
      );
      if (me.is_premium) upgradeBtn.hidden = true;
      else upgradeBtn.hidden = false;

      if (!me.has_birth_data) {
        chartEl.innerHTML = `<div class="error">
          Нет данных рождения. Откройте бота и пройдите регистрацию через /start.
        </div>`;
        return;
      }

      await loadChartSvg();
      const chart = await jget("/api/chart");
      renderSummary(chart);
      renderPlanets(chart);
      renderAspects(chart);
    } catch (e) {
      setStatus("Ошибка");
      chartEl.innerHTML = `<div class="error">
        Не удалось загрузить данные. Откройте мини-приложение из чата с ботом.
        <br/>(${e.message})
      </div>`;
    }
  }

  readingBtn.addEventListener("click", () => {
    if (tg) {
      tg.sendData("request_chart_reading");
      tg.close();
    }
  });

  upgradeBtn.addEventListener("click", () => {
    if (tg) {
      tg.sendData("open_subscriptions");
      tg.close();
    }
  });

  loadAll();
})();
