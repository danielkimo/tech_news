# 科技脈動 TechPulse - iOS App

將「每日科技新聞聚合網站」包裝成原生 iOS App。技術上採用 **WKWebView 包裝網站**
的方式：App 本體是一個輕量的 SwiftUI 殼，內部用 `WKWebView` 載入 Flask 後端網站，
這樣網站的所有功能（來源篩選、即時抓取、點擊看原文）不需要重寫就能在 iOS 上使用。

## App 名稱與 Icon

- **App 名稱**：科技脈動 TechPulse（呼應網站「即時、脈動更新」的科技新聞聚合特色）
- **App Icon**：紫色漸層背景（呼應網站主色 `#4f46e5` → `#7c3aed`），中央是一張
  白色新聞卡片搭配脈動心跳線條，右上角有一顆綠色「Live」指示點，
  對應網站首頁 Hero 區的即時抓取意象。Icon 原始設計檔與產生腳本見下方「重新產生 Icon」。

## 點新聞看原文後如何返回列表

在 App 裡點擊新聞卡片會讓 `WKWebView` 直接導航到該篇文章的原始網頁（與網站版
在新分頁開啟不同，App 只有一個 WebView 畫面）。為了避免使用者卡在文章頁面出不來，
提供三種返回新聞列表的方式：

1. **畫面下方浮動按鈕**「← 回到新聞列表」：只要還能上一頁就會顯示。
2. **導覽列左上角的返回箭頭**：同樣只在可以上一頁時顯示。
3. **系統手勢**：從畫面左邊緣向右滑動（`allowsBackForwardNavigationGestures`）。

三者都是呼叫 `WKWebView.goBack()`，效果等同瀏覽器的上一頁，會直接回到新聞列表
畫面（捲動位置、已勾選的來源/AI篩選狀態都會維持）。

## 專案結構

```
ios/
├── project.yml                  # XcodeGen 專案設定（單一事實來源）
├── TechPulse.xcodeproj/         # 由 project.yml 產生的 Xcode 專案（已包含在版控中，可直接開啟）
└── TechPulse/
    ├── TechPulseApp.swift       # App 進入點
    ├── ContentView.swift        # 主畫面：WebView + 載入中/錯誤狀態 + 重新整理/回到新聞列表按鈕
    ├── WebView.swift            # WKWebView 的 SwiftUI 包裝（含下拉重新整理、上一頁導覽）
    ├── AppConfig.swift          # 設定要載入的網址（後端伺服器位置）
    └── Assets.xcassets/
        ├── AppIcon.appiconset/  # App Icon 各尺寸圖檔
        └── AccentColor.colorset/
```

## 本機執行方式

### 1. 先啟動 Flask 後端

```bash
cd ..   # 回到專案根目錄
source .venv/bin/activate
PORT=6173 python app.py
```

### 2. 用 Xcode 開啟並執行 App

```bash
open ios/TechPulse.xcodeproj
```

在 Xcode 選擇模擬器（例如 iPhone 17）按下 ▶️ Run 即可。

- **模擬器（Simulator）測試**：`AppConfig.swift` 預設網址是
  `http://localhost:6173`，模擬器與 Mac 主機共用網路，可直接連線，不需要額外設定。
- **實體 iPhone 測試**：模擬器的 `localhost` 技巧在實機上不適用。
  請將 `AppConfig.swift` 裡的 `baseURL` 改成 Mac 在區域網路的 IP，例如：
  ```swift
  static let baseURL = URL(string: "http://192.168.1.23:6173")!
  ```
  並確認 iPhone 與 Mac 在同一個 Wi-Fi，Mac 防火牆允許連入。目前 `project.yml`
  已設定 `DEVELOPMENT_TEAM`（個人 Apple ID 的簽署 Team ID），第一次在實機上打開
  App 前，需要到 iPhone **設定 → 一般 → VPN 與裝置管理** 手動信任該開發者憑證，
  否則系統會拒絕執行未受信任的 App。個人免費簽署效期為 7 天，過期後需要
  重新用 Xcode 或下方命令列步驟重新 build 安裝一次。

### 3b. 命令列建置並直接安裝到實體 iPhone（不開 Xcode GUI）

先用 `xcrun xctrace list devices` 找出你的 iPhone 的裝置 ID，然後：

```bash
cd ios
DEVICE_ID="<你的 iPhone 裝置 ID>"

# 建置（-allowProvisioningUpdates 讓 Xcode 自動處理簽署憑證）
xcodebuild -project TechPulse.xcodeproj -scheme TechPulse \
  -destination "id=$DEVICE_ID" -configuration Debug -allowProvisioningUpdates build

# 安裝到裝置
APP_PATH="$(xcodebuild -project TechPulse.xcodeproj -scheme TechPulse \
  -destination "id=$DEVICE_ID" -configuration Debug -showBuildSettings \
  | awk -F'= ' '/ BUILT_PRODUCTS_DIR /{print $2; exit}')/TechPulse.app"
xcrun devicectl device install app --device "$DEVICE_ID" "$APP_PATH"

# 啟動
xcrun devicectl device process launch --device "$DEVICE_ID" com.danielkimo.technews.techpulse
```

### 3. 也可用命令列建置與安裝到模擬器（不開 Xcode GUI）

```bash
cd ios
xcodebuild -project TechPulse.xcodeproj -scheme TechPulse \
  -destination 'platform=iOS Simulator,name=iPhone 17' -configuration Debug build

xcrun simctl boot "iPhone 17"
xcrun simctl install booted \
  ~/Library/Developer/Xcode/DerivedData/TechPulse-*/Build/Products/Debug-iphonesimulator/TechPulse.app
xcrun simctl launch booted com.danielkimo.technews.techpulse
```

## 重新產生 Xcode 專案（若修改 project.yml）

本專案用 [XcodeGen](https://github.com/yonaskolb/XcodeGen) 從 `project.yml` 產生
`TechPulse.xcodeproj`，避免手動維護容易衝突的 `.pbxproj` 檔案。若修改了
`project.yml`（例如新增檔案、調整設定），需要重新產生：

```bash
brew install xcodegen   # 如果尚未安裝
cd ios
xcodegen generate
```

## 重新產生 App Icon

Icon 是用 Python + Pillow 程式化產生（漸層背景 + 向量繪製的新聞卡片與脈動線條），
方便未來調整配色或圖案。腳本邏輯：
1. 產生對角線漸層背景（`#4f46e5` → `#7c3aed`）。
2. 繪製白色圓角「新聞卡片」，並旋轉 -10 度增加動態感。
3. 在卡片上繪製心跳/脈動折線，代表「即時 (realtime)」。
4. 右上角加上綠色圓點（呼應網站 `.dot-live` 的即時指示）。
5. 用 4x 超取樣後縮小到 1024×1024，確保邊緣平滑。
6. 從 1024×1024 母圖縮放產生 iOS 要求的各尺寸（20/29/40/60/76/83.5pt 各種 scale）。

若要調整設計，修改後重新產生所有尺寸圖檔並覆蓋
`TechPulse/Assets.xcassets/AppIcon.appiconset/` 內的 PNG 即可，不需要改動
`Contents.json`（檔名保持一致）。

## 已知限制 / 後續可優化方向

- 目前是「網站包裝殼」而非原生 UI，若要更道地的 iOS 體驗（例如原生新聞列表、
  下拉刷新更貼近系統風格、離線快取），可以改用 SwiftUI 直接呼叫
  `/api/news` JSON API 自行渲染畫面。
- `NSAppTransportSecurity` 目前設定為允許任意連線（開發階段方便連本機 http 伺服器），
  正式上架前應改為指定網域並強制 HTTPS。
- 尚未設定簽署團隊（`DEVELOPMENT_TEAM`），首次在 Xcode 執行時需自行選擇你的
  Apple ID 對應的開發團隊才能安裝到實體裝置或上傳 App Store Connect。
