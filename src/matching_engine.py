import json
from src.jd_parser import extract_keywords


SKILL_GROUPS = {
    "硬技能": ["SQL", "Python", "Excel", "Tableau", "PowerBI", "数据分析", "埋点", "A/B", "统计", "建模"],
    "业务经验": ["用户研究", "竞品分析", "需求分析", "增长", "商业化", "运营", "B端", "C端", "SaaS"],
    "AI产品知识": ["AI", "AIGC", "大模型", "LLM", "Agent", "RAG", "Prompt", "提示词"],
    "表达包装": ["PRD", "原型", "Figma", "Axure", "项目管理", "跨部门", "沟通", "推进"],
}


def _contains(text: str, keyword: str) -> bool:
    """忽略大小写判断关键词是否出现。"""
    return keyword.lower() in text.lower()


def analyze_match(resume_text: str, jd_text: str) -> dict:
    """基于规则的岗位匹配分析，保证无 API Key 时也能演示。"""
    resume_text = resume_text or ""
    jd_text = jd_text or ""
    jd_keywords = extract_keywords(jd_text, top_n=24)

    matched = [kw for kw in jd_keywords if _contains(resume_text, kw)]
    missing = [kw for kw in jd_keywords if kw not in matched]

    keyword_score = int((len(matched) / max(len(jd_keywords), 1)) * 70)
    length_bonus = 10 if len(resume_text) > 300 and len(jd_text) > 100 else 0
    score = min(100, max(0, keyword_score + length_bonus + 15))

    if score >= 80:
        tags = ["高度匹配", "建议优先投递"]
    elif score >= 60:
        tags = ["中度匹配", "需要定制简历"]
    elif score >= 40:
        tags = ["部分匹配", "建议补强表达"]
    else:
        tags = ["匹配较弱", "谨慎投递"]

    gaps = {}
    for group, keywords in SKILL_GROUPS.items():
        group_gaps = [kw for kw in keywords if _contains(jd_text, kw) and not _contains(resume_text, kw)]
        gaps[group] = group_gaps

    strengths = [
        f"简历中已出现「{kw}」，可作为匹配 JD 要求的证据。"
        for kw in matched[:8]
    ] or ["暂未识别到明显的关键词重合，建议检查简历是否充分表达相关经历。"]

    suggestions = [
        f"如果你确实有「{kw}」相关经历，建议在项目/实习 bullet 中补充具体动作、方法和结果。"
        for kw in missing[:8]
    ] or ["当前关键词覆盖较好，建议进一步补充量化结果和业务影响。"]

    result = {
        "match_score": score,
        "match_tags": tags,
        "resume_strengths": strengths,
        "jd_high_frequency_requirements": jd_keywords[:12],
        "gap_capabilities": gaps,
        "resume_optimization_suggestions": suggestions,
        "matched_keywords": matched,
        "missing_keywords": missing[:12],
        "analysis_mode": "规则匹配 fallback",
    }
    result["analysis_json"] = json.dumps(result, ensure_ascii=False)
    return result
