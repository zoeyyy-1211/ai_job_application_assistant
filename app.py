import html
import json

import streamlit as st
import streamlit.components.v1 as components

from src.config import UPLOADS_DIR, ensure_directories, get_llm_settings
from src.dashboard import render_dashboard
from src.db import NEXT_ACTIONS, STATUSES, create_application, delete_application, get_applications, init_db, update_application
from src.llm_client import LLMClient
from src.matching_engine import GAP_LABELS, analyze_match, get_score_level
from src.resume_generator import export_resume_files, generate_resume_draft
from src.resume_parser import parse_resume
from src.utils import save_uploaded_file


POSITION_TYPES = ["AI产品", "产品经理", "项目管理", "数据分析", "运营", "其他"]
PLATFORMS = ["Boss直聘", "官网", "实习僧", "内推", "猎聘", "其他"]


def render_score(score: int) -> None:
    """按匹配度分级展示颜色和投递建议。"""
    level = get_score_level(int(score or 0))
    st.markdown(
        f"""
        <div style="border-left: 6px solid {level['color']}; padding: 10px 14px; background: #fafafa;">
          <div style="font-size: 28px; font-weight: 700; color: {level['color']};">{score} / 100</div>
          <div style="font-weight: 600;">{level['label']}：{level['advice']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_list(items: list[str], empty_text: str = "暂无") -> None:
    if not items:
        st.write(empty_text)
        return
    for item in items:
        st.write(f"- {item}")


def render_analysis_result(result: dict) -> None:
    """展示结构化岗位匹配分析结果。"""
    st.subheader("匹配分析结果")
    render_score(result.get("match_score", 0))
    st.caption(f"分析模式：{result.get('analysis_mode', '规则匹配 fallback')}")
    st.markdown("#### 总体评价")
    st.write(result.get("overall_summary", "暂无总体评价。"))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 匹配证据")
        evidence = result.get("matched_evidence", [])
        if evidence:
            for item in evidence:
                st.write(f"- 简历证据：{item.get('resume_evidence', '')}")
                st.caption(f"JD 要求：{item.get('jd_requirement', '')}")
        else:
            st.write("暂无可展示的匹配证据。")
    with col2:
        st.markdown("#### 已有优势")
        render_list(result.get("strengths", []))

    st.markdown("#### 缺口能力")
    gaps = result.get("gaps", {})
    gap_cols = st.columns(4)
    for idx, key in enumerate(["hard_skills", "business_experience", "ai_product_knowledge", "communication_packaging"]):
        with gap_cols[idx]:
            st.markdown(f"**{GAP_LABELS.get(key, key)}**")
            render_list(gaps.get(key, []), "暂未识别到明显缺口")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 简历优化建议")
        render_list(result.get("resume_suggestions", []))
    with col2:
        st.markdown("#### 面试可讲亮点")
        render_list(result.get("interview_talking_points", []))
    with col3:
        st.markdown("#### 投递风险")
        render_list(result.get("risk_warnings", []))


def tab_match_analysis() -> None:
    """岗位匹配分析 tab：上传简历、粘贴 JD、保存投递记录。"""
    st.header("岗位匹配分析")
    st.caption("支持 OpenAI-compatible API；未配置 API Key 时自动使用规则匹配 fallback。")

    with st.form("analysis_form"):
        uploaded_file = st.file_uploader("上传简历（PDF / DOCX / TXT）", type=["pdf", "docx", "txt"])
        company = st.text_input("公司名称")
        position = st.text_input("岗位名称")
        position_type = st.selectbox("岗位类型", POSITION_TYPES)
        platform = st.selectbox("投递平台", PLATFORMS)
        city = st.text_input("城市")
        application_url = st.text_input("投递链接")
        jd_text = st.text_area("粘贴岗位 JD", height=220)
        notes = st.text_area("备注", height=80)
        submitted = st.form_submit_button(
            "开始分析并保存记录",
            disabled=uploaded_file is None or not company.strip() or not position.strip() or not jd_text.strip(),
        )

    if submitted:
        if not company.strip() or not position.strip() or not jd_text.strip() or uploaded_file is None:
            st.error("请先上传简历，并填写公司名称、岗位名称和 JD。")
            return

        with st.spinner("正在解析简历并分析岗位匹配度..."):
            resume_text, error = parse_resume(uploaded_file)
            if error:
                st.error(error)
                return
            save_uploaded_file(uploaded_file, UPLOADS_DIR)

            llm_client = LLMClient()
            llm_result = llm_client.analyze(resume_text, jd_text)
            if llm_result and not llm_result.get("llm_error") and not llm_result.get("parse_failed"):
                result = llm_result
            else:
                if llm_result and llm_result.get("llm_error"):
                    st.warning(f"{llm_result['llm_error']} 已自动切换为规则匹配 fallback。")
                    if llm_result.get("raw_response"):
                        with st.expander("查看 LLM 原始返回"):
                            st.code(llm_result["raw_response"])
                result = analyze_match(resume_text, jd_text)

            application_id = create_application(
                {
                    "company": company,
                    "position": position,
                    "position_type": position_type,
                    "platform": platform,
                    "city": city,
                    "application_url": application_url,
                    "jd_text": jd_text,
                    "resume_text": resume_text,
                    "match_score": result["match_score"],
                    "status": "待投递",
                    "interview_stage": "",
                    "next_action": "修改简历",
                    "interview_notes": "",
                    "notes": notes,
                    "analysis_json": result.get("analysis_json", json.dumps(result, ensure_ascii=False)),
                }
            )

        st.success(f"分析完成，已保存投递记录 #{application_id}。")
        st.session_state["latest_analysis"] = result
        st.session_state["latest_resume_text"] = resume_text
        st.session_state["latest_jd_text"] = jd_text

        with st.expander("查看简历原文"):
            st.text_area("简历文本", resume_text, height=260)
        render_analysis_result(result)
    else:
        st.info("请上传简历并填写公司、岗位、JD 后开始分析。")


def _render_copy_button(text: str) -> None:
    escaped = json.dumps(text)
    components.html(
        f"""
        <button onclick='navigator.clipboard.writeText({escaped}).then(() => {{
          const el = document.getElementById("copy-status");
          el.textContent = "已复制到剪贴板";
        }})'>一键复制</button>
        <span id="copy-status" style="margin-left: 8px; color: #15803d;"></span>
        """,
        height=40,
    )


def tab_resume_generator() -> None:
    """定制简历生成 tab：生成、复制、导出 Markdown 和 DOCX。"""
    st.header("定制简历生成")
    st.warning("免责声明：本工具仅用于简历表达优化；不应虚构经历；用户需自行确认内容真实性。")
    analysis = st.session_state.get("latest_analysis")
    resume_text = st.session_state.get("latest_resume_text", "")
    jd_text = st.session_state.get("latest_jd_text", "")
    if not analysis:
        st.info("请先在「岗位匹配分析」中完成一次分析。")
        return

    draft = generate_resume_draft(resume_text, jd_text, analysis)
    st.text_area("定制简历草稿", draft, height=520)
    _render_copy_button(draft)

    if st.button("导出 Markdown 和 DOCX"):
        try:
            paths = export_resume_files(draft)
            st.success(f"已导出到：{paths['directory']}")
            st.download_button(
                "下载 Markdown",
                data=paths["markdown"].read_bytes(),
                file_name="tailored_resume.md",
                mime="text/markdown",
            )
            st.download_button(
                "下载 DOCX",
                data=paths["docx"].read_bytes(),
                file_name="tailored_resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        except Exception as exc:
            st.error(f"导出失败：{exc}")


def tab_applications() -> None:
    """投递记录管理 tab：筛选、更新状态、删除记录、CSV 导出。"""
    st.header("投递记录管理")
    df = get_applications()
    if df.empty:
        st.info("暂无投递记录。")
        return

    st.download_button(
        "导出全部投递记录 CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="applications.csv",
        mime="text/csv",
    )

    col1, col2, col3, col4 = st.columns(4)
    company_filter = col1.text_input("按公司筛选")
    type_filter = col2.selectbox("按岗位类型筛选", ["全部"] + sorted([x for x in df["position_type"].dropna().unique() if x]))
    status_filter = col3.selectbox("按状态筛选", ["全部"] + STATUSES)
    score_filter = col4.selectbox("按匹配度筛选", ["全部", "80-100", "60-79", "40-59", "0-39"])

    filtered = df.copy()
    filtered["match_score"] = filtered["match_score"].fillna(0).astype(int)
    if company_filter:
        filtered = filtered[filtered["company"].str.contains(company_filter, case=False, na=False)]
    if type_filter != "全部":
        filtered = filtered[filtered["position_type"] == type_filter]
    if status_filter != "全部":
        filtered = filtered[filtered["status"] == status_filter]
    if score_filter != "全部":
        low, high = [int(x) for x in score_filter.split("-")]
        filtered = filtered[(filtered["match_score"] >= low) & (filtered["match_score"] <= high)]

    if filtered.empty:
        st.info("当前筛选条件下暂无记录。")
        return

    visible_columns = [
        "id", "company", "position", "position_type", "platform", "city", "match_score",
        "status", "next_action", "interview_stage", "application_url", "created_at",
    ]
    st.dataframe(filtered[[col for col in visible_columns if col in filtered.columns]], use_container_width=True, hide_index=True)

    st.markdown("### 更新或删除记录")
    selected_id = st.selectbox("选择记录 ID", filtered["id"].tolist())
    selected_row = filtered[filtered["id"] == selected_id].iloc[0]

    with st.form("update_form"):
        new_status = st.selectbox("状态", STATUSES, index=STATUSES.index(selected_row["status"]) if selected_row["status"] in STATUSES else 0)
        next_action_value = selected_row.get("next_action") or "修改简历"
        next_action = st.selectbox(
            "下一步行动",
            NEXT_ACTIONS,
            index=NEXT_ACTIONS.index(next_action_value) if next_action_value in NEXT_ACTIONS else 0,
        )
        interview_stage = st.text_input("面试进展", value=str(selected_row.get("interview_stage") or ""))
        application_url = st.text_input("投递链接", value=str(selected_row.get("application_url") or ""))
        interview_notes = st.text_area("面试记录备注", value=str(selected_row.get("interview_notes") or ""))
        notes = st.text_area("通用备注", value=str(selected_row.get("notes") or ""))
        updated = st.form_submit_button("保存修改")
    if updated:
        update_application(int(selected_id), new_status, interview_stage, notes, application_url, next_action, interview_notes)
        st.success("记录已更新，请刷新页面或切换 tab 查看最新结果。")

    confirm_delete = st.checkbox("我确认要删除选中的记录")
    if st.button("删除记录", type="secondary"):
        if confirm_delete:
            delete_application(int(selected_id))
            st.success("记录已删除，请刷新页面或切换 tab 查看最新结果。")
        else:
            st.warning("删除前请先勾选确认框。")


def main() -> None:
    """Streamlit 应用入口。"""
    st.set_page_config(page_title="AI 秋招投递决策助手", page_icon="📌", layout="wide")
    ensure_directories()
    init_db()

    st.title("AI 秋招投递决策助手")
    settings = get_llm_settings()
    if settings["api_key"]:
        st.sidebar.success(f"已检测到 API Key，模型：{html.escape(settings['model_name'])}")
    else:
        st.sidebar.info("未配置 API Key，当前使用规则匹配 fallback。")

    tab1, tab2, tab3, tab4 = st.tabs(["岗位匹配分析", "定制简历生成", "投递记录管理", "数据看板"])
    with tab1:
        tab_match_analysis()
    with tab2:
        tab_resume_generator()
    with tab3:
        tab_applications()
    with tab4:
        render_dashboard(get_applications())


if __name__ == "__main__":
    main()
