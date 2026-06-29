def generate_resume_draft(resume_text: str, jd_text: str, analysis: dict | None = None) -> str:
    """第一阶段生成保守版简历优化草稿，不虚构经历，只提示用户基于原经历改写。"""
    analysis = analysis or {}
    suggestions = analysis.get("resume_optimization_suggestions", [])
    lines = [
        "## 定制简历草稿（规则版）",
        "",
        "说明：第一阶段不会自动编造新经历，请只基于原简历中真实发生过的内容进行替换。",
        "",
        "### 建议优先强化的 bullet",
    ]
    if suggestions:
        lines.extend([f"- {item}" for item in suggestions])
    else:
        lines.append("- 建议补充与 JD 更相关的动作、工具、结果和业务价值。")
    lines.extend([
        "",
        "### 推荐改写公式",
        "- 使用 动作 + 方法/工具 + 结果 + 业务价值 的结构。",
        "- 示例：负责 XX 分析，使用 SQL/Python 处理 XX 数据，发现 XX 问题，推动 XX 优化。",
    ])
    return "\n".join(lines)
