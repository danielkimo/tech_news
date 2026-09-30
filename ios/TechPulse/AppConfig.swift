import Foundation

/// 應用程式設定。
///
/// `baseURL` 決定 App 要載入哪個網址（也就是 Flask 後端伺服器的位置）。
///
/// - 在 iOS 模擬器（Simulator）測試時，`http://localhost:6173` 可直接連到
///   Mac 主機上執行的 `python app.py`（模擬器與主機共用網路，localhost 即代表你的 Mac）。
/// - 若要在「實體 iPhone」上測試，模擬器的 localhost 技巧不適用，
///   請改成你 Mac 在區域網路上的 IP（例如 `http://192.168.1.23:6173`），
///   並確認 iPhone 與 Mac 在同一個 Wi-Fi 網段，且防火牆允許連線。
/// - 未來若把 Flask 後端部署到正式伺服器（建議加上 HTTPS），
///   把這裡改成正式網域即可，例如 `https://technews.example.com`。
enum AppConfig {
    static let baseURL = URL(string: "http://localhost:6173")!
    static let appDisplayName = "科技脈動"
}
