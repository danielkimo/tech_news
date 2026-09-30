// 前端邏輯：勾選來源 -> 帶 query param 呼叫 /api/news -> 渲染新聞卡片列表。
// 選擇「後端 query param 重新抓取」的方式，因為抓取本身有快取，
// 重新勾選來源時只需要重新打一次 API，且能確保顯示的資料與後端快取狀態一致。

const newsListEl = document.getElementById("news-list");
const statusBarEl = document.getElementById("status-bar");
const refreshBtn = document.getElementById("refresh");
const selectAllBtn = document.getElementById("select-all");
const selectNoneBtn = document.getElementById("select-none");
const categoryBtns = document.querySelectorAll(".category-btn");

// 目前抓取到的完整新聞清單（未套用 AI 篩選前），切換 AI 篩選時直接用這份
// 資料重新渲染，不需要重打 API。
let lastFetchedItems = [];
// "all" | "ai" | "non-ai"
let currentAiFilter = "all";

function getSelectedSourceIds() {
    return Array.from(document.querySelectorAll(".source-input:checked")).map(
        (el) => el.value
    );
}

function setAllCheckboxes(checked) {
    document.querySelectorAll(".source-input").forEach((el) => {
        el.checked = checked;
    });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

function formatPublished(raw) {
    if (!raw) return "";
    const date = new Date(raw);
    if (isNaN(date.getTime())) return raw;
    return date.toLocaleString("zh-TW", { hour12: false });
}

function filterByAiCategory(items) {
    if (currentAiFilter === "ai") return items.filter((item) => item.is_ai);
    if (currentAiFilter === "non-ai") return items.filter((item) => !item.is_ai);
    return items;
}

function renderNews(items) {
    if (!items.length) {
        newsListEl.innerHTML = '<p class="empty">目前沒有符合條件的新聞，請確認至少勾選一個來源，或調整新聞類型篩選。</p>';
        return;
    }

    newsListEl.innerHTML = items
        .map(
            (item) => `
        <article class="news-card" data-link="${escapeHtml(item.link)}" data-ai="${item.is_ai ? "true" : "false"}" tabindex="0" role="link">
            <h2><a href="${escapeHtml(item.link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
                item.title
            )}</a></h2>
            <div class="news-meta">
                <span class="news-source">${escapeHtml(item.source_name)}</span>
                <span class="news-time">${escapeHtml(formatPublished(item.published))}</span>
                ${item.is_ai ? '<span class="ai-badge">🤖 AI</span>' : ""}
            </div>
            <p class="news-summary">${escapeHtml(item.summary)}</p>
            <span class="news-read-more">閱讀原文 ↗</span>
        </article>
    `
        )
        .join("");
}

function openLink(link) {
    if (!link) return;
    // 用 window.open 明確開新分頁/瀏覽器視窗，避免部分內嵌瀏覽器環境對
    // <a target="_blank"> 的支援不一致。
    const win = window.open(link, "_blank", "noopener,noreferrer");
    if (!win) {
        // 若被彈出視窗攔截，退而求其次改用當前分頁導航。
        window.location.href = link;
    }
}

// 讓整張卡片可點擊開啟原始全文；若點擊的是標題連結本身，交給瀏覽器原生
// <a> 行為處理即可，避免同時觸發兩次開啟。
newsListEl.addEventListener("click", (event) => {
    const card = event.target.closest(".news-card");
    if (!card) return;
    if (event.target.closest("a")) return;
    openLink(card.dataset.link);
});

newsListEl.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const card = event.target.closest(".news-card");
    if (!card) return;
    event.preventDefault();
    openLink(card.dataset.link);
});

function renderStatus(sources) {
    const errorEntries = Object.entries(sources).filter(([, info]) => info.status === "error");
    const total = Object.values(sources).reduce((sum, info) => sum + info.count, 0);

    const okHtml = `<span class="status-ok">✓ 已更新，共 ${total} 則新聞</span>`;
    const errorHtml = errorEntries
        .map(([, info]) => `<span class="source-error">⚠️ ${escapeHtml(info.name)} 抓取失敗</span>`)
        .join("");

    statusBarEl.innerHTML = okHtml + errorHtml;
}

async function loadNews() {
    const selectedIds = getSelectedSourceIds();
    if (!selectedIds.length) {
        lastFetchedItems = [];
        renderNews([]);
        statusBarEl.textContent = "";
        return;
    }

    newsListEl.innerHTML = `<div class="skeleton-grid">${Array(6)
        .fill(
            '<div class="skeleton-card"><div class="skeleton-line skeleton-title"></div>' +
                '<div class="skeleton-line skeleton-meta"></div>' +
                '<div class="skeleton-line"></div>' +
                '<div class="skeleton-line skeleton-short"></div></div>'
        )
        .join("")}</div>`;
    statusBarEl.textContent = "";

    try {
        const response = await fetch(`/api/news?sources=${encodeURIComponent(selectedIds.join(","))}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        lastFetchedItems = data.items;
        renderNews(filterByAiCategory(lastFetchedItems));
        renderStatus(data.sources);
    } catch (err) {
        newsListEl.innerHTML = `<p class="empty">載入新聞失敗，請稍後再試。(${escapeHtml(err.message)})</p>`;
    }
}

document.querySelectorAll(".source-input").forEach((el) => {
    el.addEventListener("change", loadNews);
});

selectAllBtn.addEventListener("click", () => {
    setAllCheckboxes(true);
    loadNews();
});

selectNoneBtn.addEventListener("click", () => {
    setAllCheckboxes(false);
    loadNews();
});

refreshBtn.addEventListener("click", loadNews);

categoryBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
        currentAiFilter = btn.dataset.aiFilter;
        categoryBtns.forEach((b) => b.classList.toggle("is-active", b === btn));
        renderNews(filterByAiCategory(lastFetchedItems));
    });
});

loadNews();
