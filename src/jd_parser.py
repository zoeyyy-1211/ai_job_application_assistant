import re
from collections import Counter


STOPWORDS = {
    "岗位", "职责", "要求", "负责", "相关", "具备", "优先", "能力", "工作", "产品",
    "项目", "以及", "进行", "完成", "支持", "参与", "了解", "熟悉", "使用", "能够",
}


ABILITY_KEYWORDS = [
    "AI", "AIGC", "大模型", "LLM", "Agent", "RAG", "Prompt", "提示词", "数据分析",
    "SQL", "Python", "Excel", "Tableau", "PowerBI", "用户研究", "竞品分析", "需求分析",
    "原型", "Axure", "Figma", "PRD", "项目管理", "沟通", "推进", "跨部门", "增长",
    "商业化", "运营", "指标", "埋点", "实验", "A/B", "B端", "C端", "SaaS",
]


def extract_keywords(text: str, top_n: int = 20) -> list[str]:
    """从 JD 中提取中文、英文和技能关键词。"""
    if not text:
        return []

    found = []
    upper_text = text.upper()
    for keyword in ABILITY_KEYWORDS:
        if keyword.upper() in upper_text:
            found.append(keyword)

    tokens = re.findall(r"[A-Za-z][A-Za-z+#./-]{1,}|[\u4e00-\u9fa5]{2,}", text)
    filtered = [token for token in tokens if token not in STOPWORDS and len(token) >= 2]
    common = [word for word, _ in Counter(filtered).most_common(top_n)]

    merged = []
    for item in found + common:
        if item not in merged:
            merged.append(item)
    return merged[:top_n]
