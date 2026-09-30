"""翻譯層（Translation Layer）。

目前為 no-op 實作：直接回傳原文，不做任何翻譯。
未來要串接 Azure OpenAI（或其他翻譯服務）時，只需要：
    1. 實作一個新的 TranslationService 子類別（例如 AzureOpenAITranslationService），
       在 translate() 方法中呼叫實際的翻譯 API。
    2. 在 get_translation_service() 中依環境變數或設定切換要使用的實作。

呼叫端（news_service.py）只需要呼叫 translate(text, target_lang) 即可，
不需要知道背後是 no-op 還是真的呼叫外部翻譯 API。
"""

from abc import ABC, abstractmethod


class TranslationService(ABC):
    """翻譯服務介面。"""

    @abstractmethod
    def translate(self, text: str, target_lang: str = "zh-Hant") -> str:
        """將 text 翻譯成 target_lang，回傳翻譯後的字串。"""
        raise NotImplementedError


class NoOpTranslationService(TranslationService):
    """目前使用的預設實作：不翻譯，直接回傳原文。"""

    def translate(self, text: str, target_lang: str = "zh-Hant") -> str:
        return text


def get_translation_service() -> TranslationService:
    """取得目前啟用的翻譯服務實例。

    未來若要切換成 Azure OpenAI 翻譯，可在此依環境變數判斷並回傳
    對應的實作，例如：

        if os.environ.get("TRANSLATION_PROVIDER") == "azure_openai":
            return AzureOpenAITranslationService(...)
        return NoOpTranslationService()
    """
    return NoOpTranslationService()


def translate(text: str, target_lang: str = "zh-Hant") -> str:
    """方便直接呼叫的輔助函式，等同於 get_translation_service().translate(...)。"""
    return get_translation_service().translate(text, target_lang)
