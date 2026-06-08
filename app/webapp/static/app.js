(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
        tg.ready();
        tg.expand();
        try { tg.setHeaderColor("#07091a"); } catch (_) {}
    }

    const initData = tg?.initData || "";

    function $(id) { return document.getElementById(id); }

    async function api(path, options = {}) {
        const headers = Object.assign({ "X-Init-Data": initData }, options.headers || {});
        const response = await fetch(path, Object.assign({}, options, { headers }));
        if (!response.ok) {
            throw new Error(`Request to ${path} failed: ${response.status}`);
        }
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
            return response.json();
        }
        return response.text();
    }

    function planetGlyph(name) {
        return ({
            Sun: "☉", Moon: "☽", Mercury: "☿", Venus: "♀", Mars: "♂",
            Jupiter: "♃", Saturn: "♄", Uranus: "♅", Neptune: "♆", Pluto: "♇",
        })[name] || "•";
    }

    function planetRu(name) {
        return ({
            Sun: "Солнце", Moon: "Луна", Mercury: "Меркурий", Venus: "Венера", Mars: "Марс",
            Jupiter: "Юпитер", Saturn: "Сатурн", Uranus: "Уран", Neptune: "Нептун", Pluto: "Плутон",
        })[name] || name;
    }

    function showError(message) {
        $("chart-wrapper").innerHTML = `<div class="loader">${message}</div>`;
    }

    async function loadProfile() {
        try {
            const profile = await api("/api/profile");
            $("greeting").textContent = profile.first_name
                ? `Здравствуй, ${profile.first_name}!`
                : "Здравствуй, искатель звёздного знания!";
            const expires = profile.plan_active_until
                ? ` до ${profile.plan_active_until.slice(0, 10)}`
                : "";
            $("plan-status").textContent =
                `Текущий план: ${profile.plan}${expires}. ` +
                `Сегодня задано ${profile.asked_today} запросов.`;
            return profile;
        } catch (e) {
            $("greeting").textContent = "Откройте мини-приложение из бота, чтобы войти.";
            $("plan-status").textContent = "Не удалось загрузить профиль.";
            console.error(e);
            return null;
        }
    }

    async function loadChart() {
        try {
            const svgText = await api("/api/chart.svg");
            $("chart-wrapper").innerHTML = svgText;
        } catch (e) {
            showError("Натальная карта ещё не создана. Откройте бота и пройдите онбординг.");
        }
    }

    async function loadSummary() {
        try {
            const summary = await api("/api/chart/summary");
            const grid = $("positions");
            grid.innerHTML = "";
            (summary.positions || []).forEach((p) => {
                const tile = document.createElement("div");
                tile.className = "planet-tile";
                const retro = p.retrograde ? " R" : "";
                const house = p.house ? ` · дом ${p.house}` : "";
                tile.innerHTML = `
                    <div class="name">${planetGlyph(p.name)} ${planetRu(p.name)}${retro}</div>
                    <div class="pos">${Math.round(p.degree_in_sign)}° ${p.sign}${house}</div>
                `;
                grid.appendChild(tile);
            });
        } catch (e) {
            $("positions").innerHTML = "";
        }
    }

    async function loadReadings() {
        try {
            const list = await api("/api/readings?limit=10");
            const root = $("readings");
            root.innerHTML = "";
            if (!list.length) {
                const empty = document.createElement("li");
                empty.textContent = "Ещё нет чтений. Начните в чате с ботом.";
                root.appendChild(empty);
                return;
            }
            list.forEach((r) => {
                const li = document.createElement("li");
                const date = new Date(r.created_at);
                const meta = document.createElement("div");
                meta.className = "meta";
                meta.textContent = `${date.toLocaleString()} · ${r.type}`;
                const body = document.createElement("div");
                body.textContent = (r.response || "").slice(0, 240);
                li.append(meta, body);
                root.appendChild(li);
            });
        } catch (e) {
            $("readings").innerHTML = "";
        }
    }

    $("open-chat").addEventListener("click", () => {
        if (tg) {
            tg.close();
        }
    });

    $("open-subscription").addEventListener("click", () => {
        if (tg && tg.sendData) {
            tg.sendData("subscription");
            tg.close();
        }
    });

    (async function bootstrap() {
        await loadProfile();
        await Promise.all([loadChart(), loadSummary(), loadReadings()]);
    })();
})();
