# AI 秋招投递决策助手

一个本地运行的 AI 求职辅助工具，面向 2027 届秋招场景，帮助用户完成岗位匹配分析、定制简历生成、投递记录管理和数据看板复盘。

当前版本：`v0.2-ai-portfolio`

## 核心功能

- 上传简历：支持 PDF、DOCX、TXT。
- 粘贴岗位 JD：填写公司、岗位、类型、平台、城市、投递链接和备注。
- AI 岗位匹配分析：支持 OpenAI-compatible API，输出结构化 JSON。
- 规则 fallback：无 API Key 或 LLM 异常时仍可完成分析。
- 定制简历生成：基于原始简历和分析结果生成 Markdown 简历草稿。
- 导出能力：支持导出定制简历 Markdown / DOCX，导出投递记录 CSV。
- 投递记录管理：支持状态、面试进展、下一步行动、投递链接和面试备注。
- 数据看板：展示投递数量、匹配度、状态分布、岗位类型、能力要求 Top 20 和投递趋势。
- 作品集文档：包含 PRD、技术设计、简历项目描述和面试 Q&A。

## 安装

```bash
cd ai_job_application_assistant
pip install -r requirements.txt
```

如果本机 `python` 命令不可用，可以使用：

```bash
python3 -m pip install -r requirements.txt
```

## 配置 LLM

复制 `.env.example` 为 `.env`，按需填写：

```env
LLM_API_KEY=
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
```

不配置 `LLM_API_KEY` 也可以运行，系统会自动使用规则匹配 fallback。

## 运行

```bash
streamlit run app.py
```

启动后，在浏览器打开 Streamlit 给出的本地地址，通常是：

```text
http://localhost:8501
```

## 项目结构

```text
ai_job_application_assistant/
  app.py
  requirements.txt
  README.md
  .env.example
  data/
  uploads/
  outputs/
  src/
    config.py
    db.py
    resume_parser.py
    jd_parser.py
    matching_engine.py
    llm_client.py
    resume_generator.py
    dashboard.py
    utils.py
  docs/
    PRD.md
    TECH_DESIGN.md
    RESUME_BULLETS.md
    INTERVIEW_QA.md
```

## 作品集讲述方式

这个项目不是一次性完成，而是按产品迭代推进：

- `v0.1-mvp`：完成本地 MVP，包括规则匹配、投递记录和基础看板。
- `v0.2-ai-portfolio`：补齐 LLM 增强分析、定制简历生成、投递管理增强、数据看板增强和作品集文档。

面试时可以围绕“用户痛点 -> MVP 验证 -> AI 增强 -> 数据复盘 -> 风险控制 -> 后续迭代”来讲。
