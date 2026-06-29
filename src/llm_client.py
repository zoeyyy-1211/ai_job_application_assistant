from src.config import get_llm_settings


class LLMClient:
    """LLM 调用占位模块，后续可接入 OpenAI、DeepSeek、通义千问等兼容接口。"""

    def __init__(self) -> None:
        self.settings = get_llm_settings()

    @property
    def is_available(self) -> bool:
        """判断是否配置 API Key；未配置时应用使用规则匹配。"""
        return bool(self.settings.get("api_key"))

    def analyze(self, resume_text: str, jd_text: str) -> dict | None:
        """第一阶段暂不调用模型，保留统一接口给后续增强。"""
        if not self.is_available:
            return None
        return None
