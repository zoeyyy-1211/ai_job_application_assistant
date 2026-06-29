from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

from src.jd_parser import extract_keywords


FOLLOW_UP_ACTIONS = {"修改简历", "准备笔试", "准备一面", "跟进 HR"}


def _prepare_dates(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["created_at_dt"] = pd.to_datetime(prepared["created_at"], errors="coerce")
    prepared["created_date"] = prepared["created_at_dt"].dt.date
    prepared["match_score"] = pd.to_numeric(prepared["match_score"], errors="coerce").fillna(0)
    return prepared


def _render_keyword_chart(df: pd.DataFrame) -> None:
    counter = Counter()
    for jd_text in df["jd_text"].fillna(""):
        counter.update(extract_keywords(jd_text, top_n=20))
    top_keywords = counter.most_common(20)
    if not top_keywords:
        st.info("暂无可统计的 JD 能力关键词。")
        return
    keyword_df = pd.DataFrame(top_keywords, columns=["能力要求", "出现次数"])
    st.plotly_chart(
        px.bar(keyword_df, x="出现次数", y="能力要求", orientation="h", title="常见 JD 能力要求 Top 20"),
        use_container_width=True,
    )


def _render_trend(df: pd.DataFrame, days: int) -> None:
    recent = df[df["created_at_dt"] >= (pd.Timestamp.now() - pd.Timedelta(days=days))]
    if recent.empty:
        st.info(f"最近 {days} 天暂无投递记录。")
        return
    trend = recent.groupby("created_date").size().reset_index(name="投递数量")
    st.plotly_chart(
        px.line(trend, x="created_date", y="投递数量", markers=True, title=f"最近 {days} 天投递趋势"),
        use_container_width=True,
    )


def render_dashboard(df: pd.DataFrame) -> None:
    """渲染增强版数据看板。"""
    if df.empty:
        st.info("暂无投递记录。完成一次岗位匹配分析并保存后，这里会显示统计图表。")
        return

    df = _prepare_dates(df)
    total = len(df)
    avg_score = round(float(df["match_score"].mean()), 1)
    high_match_count = int((df["match_score"] >= 80).sum())
    follow_up_count = int(
        df["next_action"].fillna("").isin(FOLLOW_UP_ACTIONS).sum()
        if "next_action" in df.columns
        else df[df["status"].isin(["待投递", "笔试", "一面", "二面", "HR面"])].shape[0]
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("总投递数量", total)
    col2.metric("平均匹配度", avg_score)
    col3.metric("高匹配岗位数", high_match_count)
    col4.metric("待跟进岗位数", follow_up_count)

    col_left, col_right = st.columns(2)
    with col_left:
        status_counts = df["status"].fillna("未填写").value_counts().reset_index()
        status_counts.columns = ["状态", "数量"]
        st.plotly_chart(px.bar(status_counts, x="状态", y="数量", title="投递状态分布"), use_container_width=True)
    with col_right:
        type_counts = df["position_type"].fillna("未填写").value_counts().reset_index()
        type_counts.columns = ["岗位类型", "数量"]
        st.plotly_chart(px.pie(type_counts, names="岗位类型", values="数量", title="岗位类型分布"), use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        score_df = df.copy()
        score_df["匹配度区间"] = pd.cut(
            score_df["match_score"],
            bins=[-1, 39, 59, 79, 100],
            labels=["0-39 不建议优先", "40-59 谨慎", "60-79 中等", "80-100 高匹配"],
        )
        score_counts = score_df["匹配度区间"].value_counts().sort_index().reset_index()
        score_counts.columns = ["匹配度区间", "数量"]
        st.plotly_chart(px.bar(score_counts, x="匹配度区间", y="数量", title="匹配度分布"), use_container_width=True)
    with col_right:
        avg_by_type = df.groupby("position_type", dropna=False)["match_score"].mean().round(1).reset_index()
        avg_by_type.columns = ["岗位类型", "平均匹配度"]
        st.plotly_chart(px.bar(avg_by_type, x="岗位类型", y="平均匹配度", title="不同岗位类型平均匹配度"), use_container_width=True)

    _render_keyword_chart(df)

    col_left, col_right = st.columns(2)
    with col_left:
        _render_trend(df, 7)
    with col_right:
        _render_trend(df, 30)
