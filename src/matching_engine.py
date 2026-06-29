import json
from src.jd_parser import extract_keywords


SKILL_GROUPS = {
    "hard_skills": ["SQL", "Python", "Excel", "Tableau", "PowerBI", "数据分析", "埋点", "A/B", "统计", "建模"],
    "business_experience": ["用户研究", "竞品分析", "需求分析", "增长", "商业化", "运营", "B端", "C端", "SaaS"],
    "ai_product_knowledge": ["AI", "AIGC", "大模型", "LLM", "Agent", "RAG", "Prompt", "提示词"],
    "communication_packaging": ["PRD", "原型", "Figma", "Axure", "项目管理", "跨部门", "沟通", "推进"],
}

GAP_LABELS = {
    "hard_skills": "硬技能",
    "business_experience": "业务经验",
    "ai_product_knowledge": "AI 产品知识",
    "communication_packaging": "表达包装",
}


def _contains(text: str, keyword: str) -> bool:
    """忽略大小写判断关键词是否出现。"""
    return keyword.lower() in text.lower()


def get_score_level(score: int) -> dict:
    """返回匹配度分级，用于页面展示和投递建议。"""
    if score >= 80:
        return {"label": "高匹配", "advice": "建议优先投递", "color": "#15803d"}
    if score >= 60:
        return {"label": "中等匹配", "advice": "建议定制简历后投递", "color": "#ca8a04"}
    if score >= 40:
        return {"label": "谨慎投递", "advice": "建议补强表达或选择更匹配岗位", "color": "#ea580c"}
    return {"label": "不建议优先投递", "advice": "当前匹配较弱，可先作为信息收集", "color": "#dc2626"}


def normalize_analysis_result(result: dict, analysis_mode: str = "LLM 增强分析") -> dict:
    """将 LLM 或规则结果规范成页面和数据库使用的统一结构。"""
    result = result or {}
    score = int(result.get("match_score", 0) or 0)
    score = min(100, max(0, score))

    gaps = result.get("gaps") or result.get("gap_capabilities") or {}
    normalized_gaps = {}
    for key in SKILL_GROUPS:
        value = gaps.get(key, [])
        if isinstance(value, str):
            value = [value] if value else []
        normalized_gaps[key] = value if isinstance(value, list) else []

    evidence = result.get("matched_evidence", [])
    if not isinstance(evidence, list):
        evidence = []
    clean_evidence = []
    for item in evidence:
        if isinstance(item, dict):
            clean_evidence.append(
                {
                    "resume_evidence": str(item.get("resume_evidence", "")).strip(),
                    "jd_requirement": str(item.get("jd_requirement", "")).strip(),
                }
            )

    normalized = {
        "match_score": score,
        "overall_summary": str(result.get("overall_summary", "")).strip(),
        "matched_evidence": clean_evidence,
        "strengths": result.get("strengths") or result.get("resume_strengths") or [],
        "gaps": normalized_gaps,
        "resume_suggestions": result.get("resume_suggestions") or result.get("resume_optimization_suggestions") or [],
        "interview_talking_points": result.get("interview_talking_points") or [],
        "risk_warnings": result.get("risk_warnings") or [],
        "analysis_mode": result.get("analysis_mode", analysis_mode),
    }
    for key in ["strengths", "resume_suggestions", "interview_talking_points", "risk_warnings"]:
        value = normalized[key]
        if isinstance(value, str):
            normalized[key] = [value] if value else []
        elif not isinstance(value, list):
            normalized[key] = []

    if not normalized["overall_summary"]:
        level = get_score_level(score)
        normalized["overall_summary"] = f"当前岗位匹配度为 {score} 分，属于「{level['label']}」。{level['advice']}。"

    normalized["score_level"] = get_score_level(score)
    normalized["analysis_json"] = json.dumps(normalized, ensure_ascii=False)
    return normalized


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

    evidence = [
        {"resume_evidence": f"简历中出现「{kw}」", "jd_requirement": f"JD 要求或提到「{kw}」"}
        for kw in matched[:8]
    ]
    talking_points = [
        f"围绕「{kw}」准备一个真实项目/实习案例，说明你的动作、方法和结果。"
        for kw in matched[:5]
    ] or ["准备一段说明：你为什么关注该岗位，以及现有经历如何迁移到这个岗位。"]
    warnings = [
        f"JD 提到「{kw}」，但简历中暂未识别到对应表达，投递前需要核实是否有真实经历可补充。"
        for kw in missing[:5]
    ] or ["规则匹配未发现明显风险，但仍需人工确认简历内容真实性和岗位要求细节。"]

    result = normalize_analysis_result({
        "match_score": score,
        "overall_summary": f"规则分析识别到 {len(matched)} 个 JD 关键词已在简历中出现，{len(missing)} 个关键词需要进一步核实或补强表达。",
        "matched_evidence": evidence,
        "strengths": strengths,
        "gaps": gaps,
        "resume_suggestions": suggestions,
        "interview_talking_points": talking_points,
        "risk_warnings": warnings,
        "analysis_mode": "规则匹配 fallback",
    }, analysis_mode="规则匹配 fallback")
    result.update({
        "jd_high_frequency_requirements": jd_keywords[:12],
        "matched_keywords": matched,
        "missing_keywords": missing[:12],
        "gap_labels": GAP_LABELS,
    })
    result["analysis_json"] = json.dumps(result, ensure_ascii=False)
    return result
