from src.config import get_llm_settings
from src.matching_engine import normalize_analysis_result

import json
import re


SYSTEM_PROMPT = """你是一个谨慎的 AI 求职分析助手，面向 2027 届秋招场景。
你的任务是基于用户上传的原始简历和岗位 JD，输出岗位匹配分析。

硬性要求：
1. 只能基于用户提供的原始简历和 JD 做分析。
2. 不能虚构项目、实习、公司、岗位、时间、学校、奖项、数据、指标或任何经历。
3. 如果简历中没有证据，只能写“简历中暂未体现”，不能替用户补造。
4. 输出必须是合法 JSON，不要输出 Markdown，不要添加解释性前后缀。
"""


USER_PROMPT_TEMPLATE = """请分析下面的原始简历和岗位 JD，并只返回一个 JSON 对象。

JSON 字段必须包括：
- match_score：0-100 的整数岗位匹配度
- overall_summary：总体评价
- matched_evidence：数组，每条包含 resume_evidence 和 jd_requirement
- strengths：已有优势数组
- gaps：对象，包含 hard_skills、business_experience、ai_product_knowledge、communication_packaging 四个数组
- resume_suggestions：简历优化建议数组
- interview_talking_points：面试可讲亮点数组
- risk_warnings：投递风险或不匹配点数组

注意：
- matched_evidence 的 resume_evidence 必须能在原始简历中找到依据。
- resume_suggestions 只能建议如何表达已有经历，不能建议编造经历。
- risk_warnings 要指出 JD 要求但简历证据不足的地方。

原始简历：
{resume_text}

岗位 JD：
{jd_text}
"""


class LLMClient:
    """LLM 调用占位模块，后续可接入 OpenAI、DeepSeek、通义千问等兼容接口。"""

    def __init__(self) -> None:
        self.settings = get_llm_settings()

    @property
    def is_available(self) -> bool:
        """判断是否配置 API Key；未配置时应用使用规则匹配。"""
        return bool(self.settings.get("api_key"))

    def _extract_json(self, text: str) -> dict:
        """从模型输出中容错提取 JSON。"""
        text = (text or "").strip()
        if not text:
            raise ValueError("模型返回为空。")

        candidates = [text]
        code_block = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if code_block:
            candidates.insert(0, code_block.group(1).strip())

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(text[start : end + 1])

        last_error = None
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError as exc:
                last_error = exc
        raise ValueError(f"模型输出不是合法 JSON：{last_error}")

    def analyze(self, resume_text: str, jd_text: str) -> dict | None:
        """调用 OpenAI-compatible API 进行结构化岗位匹配分析。"""
        if not self.is_available:
            return None
        try:
            from openai import OpenAI
        except ImportError:
            return {
                "llm_error": "当前环境未安装 openai，请运行 pip install -r requirements.txt。",
                "analysis_mode": "LLM 调用失败",
            }

        try:
            client = OpenAI(api_key=self.settings["api_key"], base_url=self.settings["base_url"])
            response = client.chat.completions.create(
                model=self.settings["model_name"],
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(
                            resume_text=resume_text[:12000],
                            jd_text=jd_text[:8000],
                        ),
                    },
                ],
                temperature=0.2,
            )
            raw_response = response.choices[0].message.content or ""
            parsed = self._extract_json(raw_response)
            result = normalize_analysis_result(parsed, analysis_mode=f"LLM 增强分析 - {self.settings['model_name']}")
            result["raw_response"] = raw_response
            return result
        except ValueError as exc:
            return {
                "llm_error": str(exc),
                "raw_response": locals().get("raw_response", ""),
                "parse_failed": True,
                "analysis_mode": "LLM JSON 解析失败",
            }
        except Exception as exc:
            return {
                "llm_error": f"LLM 调用失败：{exc}",
                "analysis_mode": "LLM 调用失败",
            }
