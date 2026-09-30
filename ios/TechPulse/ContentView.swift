import SwiftUI

struct ContentView: View {
    @State private var isLoading = true
    @State private var loadError: String?
    @State private var reloadTrigger = 0
    @State private var canGoBack = false
    @State private var goBackTrigger = 0

    var body: some View {
        NavigationStack {
            ZStack {
                WebView(
                    url: AppConfig.baseURL,
                    isLoading: $isLoading,
                    loadError: $loadError,
                    reloadTrigger: $reloadTrigger,
                    canGoBack: $canGoBack,
                    goBackTrigger: $goBackTrigger
                )
                .ignoresSafeArea(edges: .bottom)

                if isLoading && loadError == nil {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .tint(.white)
                        .padding(14)
                        .background(.thinMaterial, in: Circle())
                }

                if let loadError {
                    errorView(message: loadError)
                }

                // 點擊新聞卡片開啟原始網頁後，畫面上顯示可以回到新聞列表的浮動按鈕。
                if canGoBack && loadError == nil {
                    VStack {
                        Spacer()
                        Button {
                            goBackTrigger += 1
                        } label: {
                            Label("回到新聞列表", systemImage: "chevron.left")
                                .font(.subheadline.weight(.semibold))
                                .padding(.horizontal, 18)
                                .padding(.vertical, 10)
                        }
                        .background(.thinMaterial, in: Capsule())
                        .shadow(color: .black.opacity(0.15), radius: 8, y: 2)
                        .padding(.bottom, 20)
                    }
                }
            }
            .navigationTitle(AppConfig.appDisplayName)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if canGoBack {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button {
                            goBackTrigger += 1
                        } label: {
                            Image(systemName: "chevron.left")
                        }
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        reloadTrigger += 1
                    } label: {
                        Image(systemName: "arrow.clockwise")
                    }
                }
            }
        }
    }

    private func errorView(message: String) -> some View {
        VStack(spacing: 16) {
            Image(systemName: "wifi.exclamationmark")
                .font(.system(size: 40))
                .foregroundStyle(.secondary)

            Text("無法連線到伺服器")
                .font(.headline)

            Text(connectionHint(message))
                .font(.footnote)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)

            Button("重試") {
                reloadTrigger += 1
            }
            .buttonStyle(.borderedProminent)
        }
        .padding()
        .background(.regularMaterial)
    }

    private func connectionHint(_ message: String) -> String {
        """
        \(message)

        請確認本機是否已啟動後端伺服器（python app.py），
        且 App 設定的網址（AppConfig.baseURL）與伺服器位置一致。
        實機測試需改用 Mac 的區網 IP，不能使用 localhost。
        """
    }
}

#Preview {
    ContentView()
}
