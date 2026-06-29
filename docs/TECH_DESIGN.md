# TECH DESIGN：AI 秋招投递决策助手

## 1. 系统架构

项目采用本地 Streamlit 应用架构：

- 前端与交互层：`app.py`
- 配置管理：`src/config.py`
- 简历解析：`src/resume_parser.py`
- JD 关键词提取：`src/jd_parser.py`
- LLM 分析：`src/llm_client.py`
- 规则 fallback：`src/matching_engine.py`
- 简历生成与导出：`src/resume_generator.py`
- 数据库：`src/db.py`
- 数据看板：`src/dashboard.py`

## 2. 模块说明

- `resume_parser`：根据文件扩展名解析 TXT、PDF、DOCX。
- `llm_client`：读取 LLM 配置，调用 OpenAI-compatible Chat Completions。
- `matching_engine`：提供规则版匹配分析，并规范化 LLM / fallback 输出结构。
- `db`：使用 SQLite 保存投递记录，启动时自动补充新增字段。
- `dashboard`：基于投递记录生成指标卡片和图表。

## 3. LLM 调用链路

1. 用户提交简历和 JD。
2. Streamlit 调用 `parse_resume` 得到简历文本。
3. 如果配置了 `LLM_API_KEY`，调用 `LLMClient.analyze`。
4. 如果 LLM 成功返回合法 JSON，进入页面展示和数据库保存。
5. 如果没有 API Key、调用失败或 JSON 解析失败，使用 `analyze_match` 规则 fallback。

## 4. Prompt 设计

Prompt 明确要求：

- 只能基于用户提供的原始简历和 JD。
- 不能虚构项目、实习、公司、岗位、时间、学校、奖项、数据、指标。
- 如果简历中没有证据，只能写“简历中暂未体现”。
- 输出必须是合法 JSON。

## 5. JSON 输出结构

```json
{
  "match_score": 85,
  "overall_summary": "总体评价",
  "matched_evidence": [
    {
      "resume_evidence": "简历中的真实证据",
      "jd_requirement": "JD 中的岗位要求"
    }
  ],
  "strengths": ["已有优势"],
  "gaps": {
    "hard_skills": [],
    "business_experience": [],
    "ai_product_knowledge": [],
    "communication_packaging": []
  },
  "resume_suggestions": ["简历优化建议"],
  "interview_talking_points": ["面试可讲亮点"],
  "risk_warnings": ["投递风险"]
}
```

## 6. 数据库设计

`applications` 表保存投递记录：

- 基础信息：公司、岗位、岗位类型、平台、城市、投递链接。
- 输入信息：JD 文本、简历文本。
- 分析信息：匹配度、分析 JSON。
- 流程信息：状态、面试进展、下一步行动、面试备注、通用备注。
- 时间信息：创建时间、更新时间。

新增字段通过 `ALTER TABLE` 兼容迁移，不删除旧数据。

## 7. 异常处理

- 简历解析失败：页面显示具体错误。
- 未配置 API Key：自动使用规则 fallback。
- LLM 调用失败：页面展示友好提示，并使用规则 fallback。
- LLM JSON 解析失败：展示原始返回，避免页面崩溃。
- DOCX 导出失败：展示导出错误。

## 8. 隐私与安全

- 默认本地运行，数据库和上传文件保存在本机。
- `.env`、数据库、上传文件和输出文件不进入 Git。
- LLM 调用会将简历和 JD 发送到配置的模型服务，用户需要自行确认服务方可信。
- 简历生成明确提示不得虚构经历，最终内容需要用户人工确认。
