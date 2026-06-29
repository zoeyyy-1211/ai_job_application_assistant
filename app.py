import json

import pandas as pd
import streamlit as st

from src.config import UPLOADS_DIR, ensure_directories, get_llm_settings
from src.dashboard import render_dashboard
from src.db import STATUSES, create_application, delete_application, get_applications, init_db, update_application
from src.llm_client import LLMClient
from src.matching_engine import analyze_match
from src.resume_generator import generate_resume_draft
from src.resume_parser import parse_resume
from src.utils import save_uploaded_file


POSITION_TYPES = ["AI产品", "产品经理", "项目管理", "数据分析", "运营", "其他"]
PLATFORMS = ["Boss直聘", "官网", "实习僧", "内推", "猎聘", "其他"]


def render_analysis_result(result: dict) -> None:
    """展示规则版岗位匹配分析结果。"""
    st.subheader("匹配分析结果")
    st.metric("总体匹配度", f"{result['match_score']} / 100")
    st.write("匹配标签：", " / ".join(result.get("match_tags", [])))
    st.caption(f"分析模式：{result.get('analysis_mode', '规则匹配 fallback')}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 简历中已有优势")
        for item in result.get("resume_strengths", []):
            st.write(f"- {item}")
    with col2:
        st.markdown("#### JD 中高频要求")
        st.write("、".join(result.get("jd_high_frequency_requirements", [])) or "暂无")

    st.markdown("#### 缺口能力")
    gaps = result.get("gap_capabilities", {})
    for group, items in gaps.items():
        st.write(f"**{group}**：{('、'.join(items) if items else '暂未识别到明显缺口')}")

    st.markdown("#### 简历优化建议")
    for item in result.get("resume_optimization_suggestions", []):
        st.write(f"- {item}")


def tab_match_analysis() -> None:
    """岗位匹配分析 tab：上传简历、粘贴 JD、保存投递记录。"""
    st.header("岗位匹配分析")
    st.caption("第一阶段使用规则匹配，不依赖 API Key；后续可接入 LLM 增强。")

    with st.form("analysis_form"):
        uploaded_file = st.file_uploader("上传简历（PDF / DOCX / TXT）", type=["pdf", "docx", "txt"])
        company = st.text_input("公司名称")
        position = st.text_input("岗位名称")
        position_type = st.selectbox("岗位类型", POSITION_TYPES)
        platform = st.selectbox("投递平台", PLATFORMS)
        city = st.text_input("城市")
        jd_text = st.text_area("粘贴岗位 JD", height=220)
        notes = st.text_area("备注", height=80)
        submitted = st.form_submit_button("开始分析并保存记录")

    if submitted:
        if not company.strip() or not position.strip():
            st.error("请填写公司名称和岗位名称。")
            return
        if not jd_text.strip():
            st.error("请粘贴岗位 JD。")
            return

        resume_text, error = parse_resume(uploaded_file)
        if error:
            st.error(error)
            return
        save_uploaded_file(uploaded_file, UPLOADS_DIR)

        llm_client = LLMClient()
        llm_result = llm_client.analyze(resume_text, jd_text)
        result = llm_result or analyze_match(resume_text, jd_text)

        application_id = create_application(
            {
                "company": company,
                "position": position,
                "position_type": position_type,
                "platform": platform,
                "city": city,
                "jd_text": jd_text,
                "resume_text": resume_text,
                "match_score": result["match_score"],
                "status": "待投递",
                "interview_stage": "",
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


def tab_resume_generator() -> None:
    """定制简历生成 tab：第一阶段提供规则版草稿。"""
    st.header("定制简历生成")
    analysis = st.session_state.get("latest_analysis")
    resume_text = st.session_state.get("latest_resume_text", "")
    jd_text = st.session_state.get("latest_jd_text", "")
    if not analysis:
        st.info("请先在「岗位匹配分析」中完成一次分析。")
        return
    draft = generate_resume_draft(resume_text, jd_text, analysis)
    st.text_area("定制简历草稿", draft, height=360)


def tab_applications() -> None:
    """投递记录管理 tab：筛选、更新状态、删除记录。"""
    st.header("投递记录管理")
    df = get_applications()
    if df.empty:
        st.info("暂无投递记录。")
        return

    col1, col2, col3 = st.columns(3)
    company_filter = col1.text_input("按公司筛选")
    type_filter = col2.selectbox("按岗位类型筛选", ["全部"] + sorted([x for x in df["position_type"].dropna().unique() if x]))
    status_filter = col3.selectbox("按状态筛选", ["全部"] + STATUSES)

    filtered = df.copy()
    if company_filter:
        filtered = filtered[filtered["company"].str.contains(company_filter, case=False, na=False)]
    if type_filter != "全部":
        filtered = filtered[filtered["position_type"] == type_filter]
    if status_filter != "全部":
        filtered = filtered[filtered["status"] == status_filter]

    st.dataframe(
        filtered[["id", "company", "position", "position_type", "platform", "city", "match_score", "status", "interview_stage", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### 更新或删除记录")
    selected_id = st.selectbox("选择记录 ID", filtered["id"].tolist())
    selected_row = filtered[filtered["id"] == selected_id].iloc[0]

    with st.form("update_form"):
        new_status = st.selectbox("状态", STATUSES, index=STATUSES.index(selected_row["status"]) if selected_row["status"] in STATUSES else 0)
        interview_stage = st.text_input("面试进展", value=str(selected_row.get("interview_stage") or ""))
        notes = st.text_area("备注", value=str(selected_row.get("notes") or ""))
        updated = st.form_submit_button("保存修改")
    if updated:
        update_application(int(selected_id), new_status, interview_stage, notes)
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
        st.sidebar.success("已检测到 API Key，后续可启用 LLM 增强。")
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
