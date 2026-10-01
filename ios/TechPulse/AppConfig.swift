import Foundation

/// 應用程式設定。
///
/// `baseURL` 決定 App 要載入哪個網址（也就是 Flask 後端伺服器的位置）。
///
/// - 在 iOS 模擬器（Simulator）測試時，`http://localhost:6173` 可直接連到
///   Mac 主機上執行的 `python app.py`（模擬器與主機共用網路，localhost 即代表你的 Mac）。
/// - 若在「實體 iPhone」且與 Mac 連同一個 Wi-Fi 網段，可改成 Mac 的區網 IP
///   （例如 `http://192.168.1.23:6173`）。缺點是手機切到行動網路（5G/4G）
///   或換 Wi-Fi 後就連不到，因為區網 IP 只有同一個路由器底下才能互通。
/// - 若要讓手機在「任何網路」（含 5G）都能連線，可用 cloudflared/ngrok 之類的
///   工具把本機 Flask 服務建立一個公開網址（例如
///   `cloudflared tunnel --url http://localhost:6173`），把產生的
///   `https://xxxx.trycloudflare.com` 網址填在這裡即可。注意：免費版 quick
///   tunnel 每次重啟網址都會變，僅適合臨時測試；長期使用請考慮正式部署
///   （見下一點）或申請固定的 named tunnel。
/// - 未來若把 Flask 後端部署到正式伺服器（建議加上 HTTPS），
///   把這裡改成正式網域即可，例如 `https://technews.example.com`。
enum AppConfig {
    // 目前設定為 cloudflared 臨時公開網址，讓手機在 Wi-Fi 或 5G 行動網路下
    // 都能連線測試。此網址會在 cloudflared 重啟後失效，需要重新產生並更新。
    static let baseURL = URL(string: "https://chicago-ant-bones-korean.trycloudflare.com")!
    static let appDisplayName = "科技脈動"
}
