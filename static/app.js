// 前端邏輯：勾選來源 -> 帶 query param 呼叫 /api/news -> 渲染新聞卡片列表。
// 選擇「後端 query param 重新抓取」的方式，因為抓取本身有快取，
// 重新勾選來源時只需要重新打一次 API，且能確保顯示的資料與後端快取狀態一致。

const newsListEl = document.getElementById("news-list");
const statusBarEl = document.getElementById("status-bar");
const refreshBtn = document.getElementById("refresh");
const selectAllBtn = document.getElementById("select-all");
const selectNoneBtn = document.getElementById("select-none");

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

function renderNews(items) {
    if (!items.length) {
        newsListEl.innerHTML = '<p class="empty">目前沒有符合條件的新聞，請確認至少勾選一個來源。</p>';
        return;
    }

    newsListEl.innerHTML = items
        .map(
            (item) => `
        <article class="news-card">
            <h2><a href="${escapeHtml(item.link)}" target="_blank" rel="noopener noreferrer">${escapeHtml(
                item.title
            )}</a></h2>
            <div class="news-meta">
                <span class="news-source">${escapeHtml(item.source_name)}</span>
                <span class="news-time">${escapeHtml(formatPublished(item.published))}</span>
            </div>
            <p class="news-summary">${escapeHtml(item.summary)}</p>
        </article>
    `
        )
        .join("");
}

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
        renderNews(data.items);
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

loadNews();
