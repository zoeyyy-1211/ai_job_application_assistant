# AI 秋招投递决策助手

一个本地运行的 AI 求职辅助工具，面向 2027 届秋招场景，帮助用户完成岗位匹配分析、简历优化建议、投递记录管理和数据看板复盘。

第一阶段 MVP 使用规则匹配，不强依赖 LLM。即使没有 API Key，也可以完成简历上传、JD 分析和投递记录保存。

## 功能

- 上传简历：支持 PDF、DOCX、TXT。
- 粘贴岗位 JD：支持填写公司、岗位、类型、平台、城市和备注。
- 基础匹配分析：输出匹配度、匹配标签、已有优势、JD 高频要求、缺口能力和优化建议。
- 投递记录管理：支持查看、筛选、更新状态、删除记录。
- 数据看板：展示总投递数、平均匹配度、状态分布和岗位类型分布。
- LLM 接口占位：支持通过 `.env` 配置 OpenAI-compatible API，后续可增强分析能力。

## 安装

```bash
cd ai_job_application_assistant
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，按需填写：

```bash
API_KEY=
BASE_URL=https://api.openai.com/v1
MODEL_NAME=gpt-4o-mini
```

不配置 API Key 也可以运行，系统会使用规则匹配 fallback。

## 运行

```bash
streamlit run app.py
```

启动后，在浏览器打开 Streamlit 给出的本地地址。

## 第一阶段测试方式

1. 准备一份 TXT、PDF 或 DOCX 简历。
2. 打开「岗位匹配分析」tab。
3. 上传简历，填写公司、岗位、岗位类型、平台、城市。
4. 粘贴一段岗位 JD。
5. 点击「开始分析并保存记录」。
6. 查看匹配分析结果。
7. 打开「投递记录管理」，检查记录是否保存。
8. 修改状态或面试进展。
9. 打开「数据看板」，检查统计卡片和图表是否更新。

## 项目结构

```text
ai_job_application_assistant/
  app.py
  requirements.txt
  README.md
  .env.example
  data/applications.db
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
  docs/PRD.md
```

## 后续迭代

- 接入真实 LLM 分析，输出结构化 JSON。
- 生成更完整的定制简历版本。
- 增加分析结果详情页。
- 增加投递记录编辑更多字段。
- 增加高频能力要求统计和趋势分析。
